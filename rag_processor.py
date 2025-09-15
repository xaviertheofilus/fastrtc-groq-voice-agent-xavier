import os
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate
import logging

logger = logging.getLogger(__name__)

class RAGProcessor:
    def __init__(self, data_folder="data"):
        self.data_folder = data_folder
        self.vectorstore = None
        self.qa_chain = None
        self.embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2"
        )
        self.llm = Ollama(model="phi")
        self.has_documents = False
        self.setup_qa_chain()
        
    def load_documents(self):
        documents = []
        if not os.path.exists(self.data_folder):
            os.makedirs(self.data_folder, exist_ok=True)
            return documents
            
        for filename in os.listdir(self.data_folder):
            file_path = os.path.join(self.data_folder, filename)
            try:
                logger.info(f"Loading document: {filename}")
                if filename.endswith(".pdf"):
                    loader = PyPDFLoader(file_path)
                elif filename.endswith(".txt"):
                    loader = TextLoader(file_path, encoding="utf-8")
                else:
                    continue
                
                documents.extend(loader.load())
            except Exception as e:
                logger.error(f"Error loading {filename}: {str(e)}")
                continue
        
        return documents
    
    def setup_qa_chain(self):
        documents = self.load_documents()
        
        if not documents:
            logger.warning("No documents available for RAG setup")
            self.has_documents = False
            self.qa_chain = None
            return None
            
        try:
            # Create vector store with FAISS
            self.vectorstore = FAISS.from_documents(documents, self.embeddings)
            
            # Custom prompt untuk konteks Indonesia
            prompt_template = """Anda adalah asisten AI yang membantu pengguna. 
            Gunakan konteks berikut untuk menjawab pertanyaan. 
            Jika jawaban tidak ditemukan dalam konteks, jelaskan bahwa Anda tidak memiliki informasi yang cukup 
            dan tawarkan untuk membantu dengan pertanyaan umum.
            
            Konteks: {context}
            
            Pertanyaan: {question}
            Jawaban dalam Bahasa Indonesia:"""
            
            PROMPT = PromptTemplate(
                template=prompt_template, input_variables=["context", "question"]
            )
            
            # Create QA chain
            self.qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=self.vectorstore.as_retriever(search_kwargs={"k": 3}),
                chain_type_kwargs={"prompt": PROMPT},
                return_source_documents=False
            )
            self.has_documents = True
            logger.info("RAG QA chain setup completed successfully")
            return self.qa_chain
        except Exception as e:
            logger.error(f"Error setting up QA chain: {str(e)}")
            self.has_documents = False
            return None
    
    def query(self, question: str):
        # Jika tidak ada dokumen, gunakan LLM langsung untuk percakapan umum
        if not self.has_documents:
            try:
                # Prompt untuk percakapan umum dalam bahasa Indonesia
                general_prompt = f"""Anda adalah asisten AI yang membantu pengguna. 
                Jawablah pertanyaan berikut dengan ramah dan informatif menggunakan bahasa Indonesia.
                
                Jika Anda tidak tahu jawabannya, jangan membuat-buat jawaban.
                Katakan saja bahwa Anda belum memiliki pengetahuan tentang topik tersebut 
                dan sarankan pengguna untuk mengupload dokumen PDF terkait.
                
                Pertanyaan: {question}
                Jawaban:"""
                
                response = self.llm(general_prompt)
                return response
            except Exception as e:
                logger.error(f"Error in general conversation: {str(e)}")
                return "Maaf, saya mengalami gangguan teknis. Silakan coba lagi dalam beberapa saat."
        
        # Jika ada dokumen, gunakan RAG
        try:
            result = self.qa_chain({"query": question})
            return result["result"]
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            # Fallback ke percakapan umum jika RAG gagal
            try:
                fallback_prompt = f"""Jawablah pertanyaan berikut dengan ramah menggunakan bahasa Indonesia.
                
                Pertanyaan: {question}
                Jawaban:"""
                
                return self.llm(fallback_prompt)
            except Exception as e2:
                logger.error(f"Error in fallback conversation: {str(e2)}")
                return "Maaf, terjadi kesalahan dalam memproses pertanyaan Anda. Silakan coba lagi."