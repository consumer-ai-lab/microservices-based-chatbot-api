from langchain.prompts import PromptTemplate
from langchain_google_genai import GoogleGenerativeAIEmbeddings,ChatGoogleGenerativeAI
from langchain.chains import RetrievalQA
from langchain.vectorstores.pgvector import PGVector
import google.generativeai as genai
from dotenv import find_dotenv, load_dotenv
import os

from langchain.globals import set_debug

set_debug(True)

load_dotenv(find_dotenv())
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

class QueryManager:
    def __init__(self):
        self.connection_string = os.getenv('CONNECTION_STRING')
        self.collection_name = os.getenv('CONNECTION_NAME')
    
    def get_custom_prompt(self):
        prompt_template = """
        As an advanced and reliable medical chatbot, your foremost priority is to furnish the user with precise, evidence-based health insights and guidance. It is of utmost importance that you strictly adhere to the context provided, without introducing assumptions or extrapolations beyond the given information. Your responses must be deeply rooted in verified medical knowledge and practices. Additionally, you are to underscore the necessity for users to seek direct consultation from healthcare professionals for personalized advice.

        In crafting your response, it is crucial to:
        - Confine your analysis and advice strictly within the parameters of the context provided by the user. Do not deviate or infer details not explicitly mentioned.
        - Identify the key medical facts or principles pertinent to the user's inquiry, applying them directly to the specifics of the provided context.
        - Offer general health information or clarifications that directly respond to the user's concerns, based solely on the context.
        - Discuss recognized medical guidelines or treatment options relevant to the question, always within the scope of general advice and clearly bounded by the context given.
        - Emphasize the critical importance of professional medical consultation for diagnoses or treatment plans, urging the user to consult a healthcare provider.
        - Where applicable, provide actionable health tips or preventive measures that are directly applicable to the context and analysis provided, clarifying these are not substitutes for professional advice.

        Your aim is to deliver a response that is not only informative and specific to the user's question but also responsibly framed within the limitations of non-personalized medical advice. Ensure accuracy, clarity, and a strong directive for the user to seek out professional medical evaluation and consultation. Through this approach, you will assist in enhancing the user's health literacy and decision-making capabilities, always within the context provided and without overstepping the boundaries of general medical guidance.

        context: {context}
        
        Question: {question}

        """

        prompt = PromptTemplate(template=prompt_template,input_variables=['context','question'])
        return prompt
    
    def get_retriever(self):
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        store = PGVector(
            collection_name=self.collection_name,
            connection_string=self.connection_string,
            embedding_function=embeddings
        )
        return store.as_retriever(search_kwargs={'k':5})
    
    def get_retrival_qa_chain(self):
        prompt = self.get_custom_prompt()
        retriever = self.get_retriever()
        llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.5,convert_system_message_to_human=True)
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type='stuff',
            retriever=retriever,
            return_source_documents=False,
            chain_type_kwargs={'prompt':prompt}
        )
        return qa_chain
    
    def get_response(self, query: str)->str:
        bot = self.get_retrival_qa_chain()
        res = bot.invoke(query)
        return res.get("result")
    
def get_query_manager()->QueryManager:
    return QueryManager()