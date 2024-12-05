import os,json,logging,sys,requests
import pandas as pd
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
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    if not url:
        with open(path) as json_file:
            schema_data = json.load(json_file)
            return schema_data
    else:
        data_from_url = requests.get(schema)
        schema_data = json.loads(data_from_url.content)
        return schema_data
        
# Create Search Index from the schema
# If reading the schema from a URL, set url=True
def create_schema_from_json_and_upload(schema, index_name, admin_client, url=False):

    cors_options = CorsOptions(allowed_origins=["*"], max_age_in_seconds=60)
    scoring_profiles:List[ScoringProfile] = []
    schema_data = get_schema_data(schema, url)

    index = SearchIndex(
        name=index_name,
        fields=schema_data['fields'],
        scoring_profiles=scoring_profiles,
        suggesters=schema_data['suggesters'],
        cors_options=cors_options
    )

    try:
        upload_schema = admin_client.create_index(index)
        if upload_schema:
            print(f"Schema uploaded; Index created for {index_name}.")
        else:
            exit(0)
    except Exception as ex:
        print("Unexpected error:",sys.exc_info()[0])


# Convert CSV data to JSON
def convert_csv_to_json(url):
    df = pd.read_csv(url)
    df = pd.read_csv(url)
    convert = df.to_json(orient='records')
    return json.loads(convert)

# Batch your uploads to Azure Search
def batch_upload_json_data_to_index(json_file, client):
    batch_array = []
    count = 0
    batch_counter = 0
    for i in json_file:
        count+=1
        batch_array.append(
            {
                "id": str(i["book_id"]),
                "goodreads_book_id": int(i["goodreads_book_id"]),
                "best_book_id": int(i["best_book_id"]),
                "work_id": int(i["work_id"]),
                "books_count": i["books_count"] if i["books_count"] else 0,
                "isbn": str(i["isbn"]),
                "isbn13": str(i["isbn13"]),
                "authors": i["authors"].split(",") if i["authors"] else None,
                "original_publication_year":int(i["original_publication_year"]) if i["original_publication_year"] else 0,
                "original_title":i["original_title"],
                "title":i["title"],
                "language_code":i["language_code"],
                "average_rating":int(i["average_rating"]) if i["average_rating"] else 0,
                "ratings_count":int(i["ratings_count"]) if i["ratings_count"] else 0,
                "work_ratings_count":int(i["work_ratings_count"]) if i["work_ratings_count"] else 0,
                "work_text_reviews_count":i["work_text_reviews_count"] if i["work_text_reviews_count"] else 0,
                "ratings_1":int(i["ratings_1"]) if i["ratings_1"] else 0,
                "ratings_2":int(i["ratings_2"]) if i["ratings_2"] else 0,
                "ratings_3":int(i["ratings_3"]) if i["ratings_3"] else 0,
                "ratings_4":int(i["ratings_4"]) if i["ratings_4"] else 0,
                "ratings_5":int(i["ratings_5"]) if i["ratings_5"] else 0,
                "image_url":i["image_url"],
                "small_image_url":i["small_image_url"],
            }
        )

        # In this sample, we limit batches to 1000 records.
        # When the counter hits a number divisible by 1000, the batch is sent.
        if count % batch_size == 0:
            client.upload_documents(documents=batch_array)
            batch_counter += 1
            print(f"Batch sent! - #{batch_counter}")
            batch_array = []

    # This will catch any records left over, when not divisible by 1000
    if len(batch_array) > 0:
        client.upload_documents(documents=batch_array)
        batch_counter += 1
        print(f"Final batch sent! - #{batch_counter}")

    print("Done!")

if __name__ == "__main__":
    start_client = CreateClient(service_endpoint, key, index_name)
    admin_client = start_client.create_admin_client()
    search_client = start_client.create_search_client()
    schema = create_schema_from_json_and_upload(index_schema, index_name, admin_client, url=False)
    books_data = convert_csv_to_json(books_url)
    batch_upload = batch_upload_json_data_to_index(books_data, search_client)
    print("Upload complete!")