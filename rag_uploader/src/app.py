from fastapi import FastAPI,UploadFile,File,Response,BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from .vector_store_manager import get_vector_store_manager
import os
import copy

app = FastAPI(root_path='/api/rag')
app.add_middleware(
    CORSMiddleware, 
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

vector_store_manager = get_vector_store_manager()

@app.get("/")
def root():
    return {"message":"hello from rag_uploader"}

@app.get('/test')
def test_vector_database(query:str):
    vector_store_manager.test_query(query=query)
    return Response(content="see the logs",status_code=200)

def vectorize_file(file:UploadFile):
    try:
        try:
            os.makedirs('./temp_data', exist_ok=True)
            file.file.seek(0)
            content=file.file.read() 
            with open(f'./temp_data/{file.filename}','wb') as f:
                f.write(content)
        except:
            print("there was error while processing the file")
        finally:
            file.file.close()
        vector_store_manager.generate_vector_store(f'./temp_data/{file.filename}')
        os.remove(f'./temp_data/{file.filename}')
        print("Successfully created the vector embeddings.")
    except:
        print("there was error while creating the vector embeddings for the file.")


@app.post('/upload')
async def upload_file(file:UploadFile=File(...), background_tasks: BackgroundTasks=BackgroundTasks()):
    max_size=50*1024*1024
    try:
        size = 0
        for chunk in file.file:
            size += len(chunk)
            if size > max_size:
                return Response(content="file too large",status_code=413)
        allowed_file_types = ["application/pdf"]
        if file.content_type not in allowed_file_types:
            return Response(content="invalid file type",status_code=415)
        
        background_tasks.add_task(vectorize_file,file=copy.deepcopy(file))
        
        return Response(content="Started processing the file...",status_code=200)
    except Exception as e:
        print("Error processing file: %s", e) 
        return Response(content="there was error processing thei  file",status_code=500)