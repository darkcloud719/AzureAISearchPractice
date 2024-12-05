import os,json,logging,sys
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import QueryType, QueryCaptionType, QueryAnswerType, QueryCaptionResult, QueryAnswerResult
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
    SemanticConfiguration,
    SemanticField,
    SemanticPrioritizedFields,
    SemanticSearch
)
from dotenv import load_dotenv
from typing import List

load_dotenv()

service_endpoint = os.getenv("AZURE_SEARCH_SERVICE_ENDPOINT")
key = os.getenv("AZURE_SEARCH_API_KEY")
index_name = "good-books"

index_schema = "good-books-index.json"

books_url = "https://raw.githubusercontent.com/Azure-Samples/azure-search-sample-data/main/good-books/books.csv"
batch_size = 1000

class CreateClient(object):
    def __init__(self, endpoint, key, index_name):
        self.endpoint = endpoint
        self.index_name = index_name
        self.key = key
        self.credentials = AzureKeyCredential(key)

    # Create a SearchClient
    # Use this to upload docs to the Index
    def create_search_client(self):
        return SearchClient(endpoint=self.endpoint, index_name=self.index_name, credential=self.credentials)
    
    def create_admin_client(self):
        return SearchIndexClient(endpoint=self.endpoint, credential=self.credentials)
    
    # Get Schema from Fiel or URL
    def get_schema_data(schema, url=False):
        path = os.path.join('..','JsonFile',schema)
        if not url:
            with open(path) as json_file:
            
        
