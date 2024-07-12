from transformers import CLIPModel, CLIPProcessor
from PIL import Image
import torch, faiss,  pandas, numpy, numpy.typing, os
import torchvision.transforms as transforms
from tqdm import tqdm
from torch.utils.data import Dataset, DataLoader
from ..model import(
    CLIP_MODEL,
    CLIP_COMP_DIM,
    CSV_FOLDER,
    IMAGE_FOLDER,
)

device:str = 'cuda'

class CLIPDataset(Dataset):
    def __init__(self, df: pandas.DataFrame, processor: CLIPProcessor, step:int= 5):
        self.transform= transforms.Compose([
            transforms.Resize((224,224)),
            transforms.PILToTensor(),
        ])

        self.processor= processor

        self.image_filenames: list[str]= df['image'].values[::step]
        self.captions: list[str]= df['caption'].values[::step]

    def __getitem__(self, idx):
        image= Image.open(f"{IMAGE_FOLDER}/{self.image_filenames[idx]}").convert('RGB')
        image_tensor= self.transform(image)

        caption= self.captions[idx]
        caption_tensor= self.processor(
            text=caption,
            return_tensors= 'pt',
            padding= 'max_length', 
            truncation=True, 
            max_length=77
        ).input_ids.squeeze()

        item = {
            'image':image_tensor,
            'caption': caption_tensor
        }

        return item
    
    def __len__(self): 
        return len(self.image_filenames)

class CLIPCompositeIndexer:
    
    def __init__(self, fp:str= 'index.faiss')-> None:\

        self._embed_model= CLIPModel.from_pretrained(CLIP_MODEL).to(device)
        self._processor= CLIPProcessor.from_pretrained(CLIP_MODEL)
        df= pandas.read_csv(CSV_FOLDER, delimiter='|')

        df.drop(' comment_number', axis=1, inplace= True)
        df.columns= ['image', 'caption']
        self.df= df
        self.dataset= CLIPDataset(self.df, self._processor) #Flickr30k dataset
        self.index= faiss.IndexFlatIP(CLIP_COMP_DIM)

        if os.path.exists(fp):
            print(f"Loading existing index from {fp}")
            self.read_index(fp)

        else:
            print(f"Creating new index and saving to {fp}")
            self.create_index()
            self.write_index(fp)
        

    def write_index(self, fp:str):
        faiss.write_index(self.index, fp)
    
    def read_index(self, fp: str):
        self.index= faiss.read_index(fp)


    def get_image_embedding(self, image_tensor: torch.Tensor)-> torch.Tensor:
        image_tensor= image_tensor.to(device)
        inputs= self._processor(
            images= image_tensor,
            return_tensors= 'pt', 
            do_resize= False, 
            do_normalize=True
        ).to(device)

        with torch.no_grad():
            image_embeddings= self._embed_model.get_image_features(**inputs)

        return image_embeddings


    def get_text_embedding(self, text_tensor: torch.Tensor)-> torch.Tensor:
        text_tensor= text_tensor.to(device)
        attention_mask= (text_tensor != self._processor.tokenizer.pad_token_id).long()

        inputs= {
            "input_ids": text_tensor,
            "attention_mask": attention_mask
        }

        with torch.no_grad():
            text_embeddings= self._embed_model.get_text_features(**inputs)

        return text_embeddings
    
    def get_composite_embedding(self, batch)-> numpy.typing.NDArray:
        image_embedding= self.get_image_embedding(batch['image'])
        text_embedding= self.get_text_embedding(batch['caption'])

        concatenated_vector= torch.cat((image_embedding, text_embedding), dim=1)
        normalized_vector= torch.nn.functional.normalize(concatenated_vector, dim=1)


        return normalized_vector.cpu().numpy()
    
    def create_index(self):
        dataloader= DataLoader(
            dataset= self.dataset,
            num_workers=28,
            batch_size=100,
            pin_memory=True
        )

        composite_embeddings= []

        for batch in tqdm(dataloader, desc="Creating index"):
            composite_embedding= self.get_composite_embedding(batch)
            composite_embeddings.append(composite_embedding)
        
        composite_embeddings= numpy.vstack(composite_embeddings)

        self.index.add(composite_embeddings)
    
    
    def search(self, query:str, k:int= 1, step:int= 5):
        query_tensor= self._processor(
            text= [query],
            return_tensors='pt',
            padding= 'max_length',
            truncation= True,
            max_length= 77,
        ).input_ids.to(device)

        query_embedding= self.get_text_embedding(query_tensor)
        paded_query_embedding= torch.nn.functional.pad(query_embedding, (0, CLIP_COMP_DIM - query_embedding.size(1)))
        normalized_paded_query_embedding= torch.nn.functional.normalize(paded_query_embedding, dim=1)
        _, idxs= self.index.search(normalized_paded_query_embedding.cpu().numpy(), k=k)
        results = []
        for idx in idxs[0]:
            orginal_idx= idx*step
            results.append({
                "image": self.df["image"][orginal_idx],
                "caption": self.df["caption"][orginal_idx],
            })
    
        return results
    
    def __call__(self, query:str):
        return self.search(query)


    


