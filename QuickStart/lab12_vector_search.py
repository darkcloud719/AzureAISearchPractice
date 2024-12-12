# azure.search-documents11.6.0b4
import os,json,logging,sys
import openai
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import QueryType, QueryCaptionType, QueryAnswerType, QueryCaptionResult, QueryAnswerResult, VectorizableTextQuery, VectorizedQuery, VectorFilterMode
from azure.search.documents.indexes import SearchIndexClient, SearchIndexerClient
from azure.search.documents.indexes.models import(
    SearchIndexerDataContainer,
    SearchIndex,
    SimpleField,
    SearchFieldDataType,
    EntityRecognitionSkill,
    SentimentSkill,
    InputFieldMappingEntry,
    OutputFieldMappingEntry,
    SearchIndexerSkillset,
    SearchableField,
    IndexingParameters,
    SearchIndexerDataSourceConnection,
    IndexingParametersConfiguration,
    IndexingSchedule,
    CorsOptions,
    SearchIndexer,
    FieldMapping,
    ScoringProfile,
    ComplexField,
    ImageAnalysisSkill,
    OcrSkill,
    VisualFeature,
    TextWeights,
    SearchField,
    SemanticConfiguration,
    SemanticField,
    SemanticPrioritizedFields,
    SemanticSearch,
    VectorSearch,
    VectorSearchAlgorithmConfiguration,
    VectorSearchProfile,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
    AzureOpenAIVectorizer,
    AzureOpenAIParameters
)
from dotenv import load_dotenv
from typing import List

load_dotenv()

service_endpoint = os.getenv("AZURE_SEARCH_SERVICE_ENDPOINT")
key = os.getenv("AZURE_SEARCH_API_KEY")
index_name = "hotels-quickstart-vector"
indexer_name = "hotels-quickstart-vector-indexer"
connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")

azure_openai_embeddings_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_FOR_EMBEDDINGS")

search_client = SearchClient(service_endpoint, index_name, AzureKeyCredential(key))
search_index_client = SearchIndexClient(service_endpoint, AzureKeyCredential(key))
search_indexer_client = SearchIndexerClient(service_endpoint, AzureKeyCredential(key))

openai.api_key = os.getenv("OPENAI_API_KEY")
openai.azure_endpoint =os.getenv("AZURE_OPENAI_ENDPOINT")
openai.api_version = os.getenv("OPENAI_API_VERSION")
openai.api_type = "azure"

def search_documents_by_similarity():

    try:
        query = "tools for software development"
        embedding = openai.embeddings.create(input=query, model=azure_openai_embeddings_deployment, dimensions=1536).data[0].embedding
        
        vector_query = VectorizedQuery(vector=embedding, k_nearest_neighbors=3, fields="contentVector")

        # print(vector_query)

        results = search_client.search(search_text="*", vector_queries=[vector_query], select=["title","content","category"])

        for result in results:
            for result_key, value in result.items():
                print(f"{result_key}:{value}")
            print("\n\n")
    except Exception as ex:
        print(ex)

def search_documents_by_cross_field():

    try:
        query = "tools for software development"

        vector_query = VectorizableTextQuery(text=query, k_nearest_neighbors=3, fields="contentVector, titleVector")

        results = search_client.search(query_type="simple", search_text="*", vector_queries=[vector_query], select=["title","content","category"])

        for result in results:
            for result_key, value in result.items():
                print(f"{result_key}:{value}")
            print("\n\n")

    except Exception as ex:
        print(ex)


def search_documents_by_multi_vector():
    
    try:
        query = "tools for software development"

        vector_query_1 = VectorizableTextQuery(text=query, k_nearest_neighbors=1, fields="titleVector")
        vector_query_2 = VectorizableTextQuery(text=query, k_nearest_neighbors=1, fields="contentVector")

        results = search_client.search(
            query_type="simple",
            search_text="*",
            vector_queries=[vector_query_1, vector_query_2],
            select=["title","content","category"],
        )

        for result in results:
            for result_key, value in result.items():
                print(f"{result_key}:{value}")
            print("\n\n")
    except Exception as ex:
        print(ex)

def search_documents_by_filter():

    try:
        query = "tools for software development"

        vector_query = VectorizableTextQuery(text=query, k_nearest_neighbors=3, fields="contentVector")

        results = search_client.search(
            search_text="*",
            vector_queries=[vector_query],
            vector_filter_mode=VectorFilterMode.POST_FILTER,
            filter="category eq 'Developer Tools'",
            select=["title","content","category"]
        )

        for result in results:
            for result_key, value in result.items():
                print(f"{result_key}:{value}")
            print("\n\n")

    except Exception as ex:
        print(ex)

def hybrid_search():

    try:
        query = "scalable storage solution"

        vector_query = VectorizableTextQuery(text=query, k_nearest_neighbors=3, fields="contentVector")

        results = search_client.search(
            query_type="simple",
            search_text=query,
            vector_queries=[vector_query],
            select=["title","content","category"],
            top=3
        )

        for result in results:
            for result_key, value in result.items():
                print(f"{result_key}:{value}")
            print("\n\n")
    except Exception as ex:
        print(ex)

def semantic_hybrid_search():

    try:
        query = "what is azure search?"

        vector_query = VectorizableTextQuery(text=query, k_nearest_neighbors=3, fields="contentVector")

        results = search_client.search(
            query_type=QueryType.SEMANTIC,
            semantic_configuration_name="my-semantic-config",
            query_caption="extractive",
            query_answer="extractive",
            search_text=query,
            vector_queries=[vector_query],
            select=["title","content","category"],
            top=3
        )

        semantic_answers = results.get_answers()

        for answer in semantic_answers:
            if answer.highlights:
                print(f"Semantic Answer: {answer.highlights}")
            else:
                print(f"Semantic Answer: {answer.text}")
            print("\n")
            print(f"Semantic Answer Score: {answer.score}\n")
        
        for result in results:
            for result_key, value in result.items():
                print(f"{result_key}:{value}")
            
            captions = result["@search.captions"]
            if captions:
                caption = captions[0]
                if caption.highlights:
                    print(f"Caption: {caption.highlights}\n")
                else:
                    print(f"Caption: {caption.text}\n")

    except Exception as ex:
        print(ex)




if __name__ == "__main__":
    # search_documents_by_similarity()
    # search_documents_by_cross_field()
    # search_documents_by_multi_vector()
    # search_documents_by_filter()
    # hybrid_search()
    semantic_hybrid_search()

