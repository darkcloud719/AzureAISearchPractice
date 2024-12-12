import os,json,logging,sys,openai
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
index_name = "hotels-quickstart-vector2",
indexer_name= "hotels-quickstart-vector_indexer2"
data_source_name = "hotels-quickstart-vector-datasource2"
connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")

azure_openai_model = "gpt-4o"
azure_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
azure_openai_model = os.getenv("OPENAI_API_KEY")
azure_openai_embedding_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_FOR_EMBEDDINGS")
azure_openai_api_version = os.getenv("OPENAI_API_VERSION")

openai.api_key = os.getenv("OPENAI_API_KEY")
openai.azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
openai.api_version = os.getenv("OPENAI_API_VERSION")
openai.api_type = "azure"

def _delete_index():

    try:
        with SearchIndexClient(service_endpoint, AzureKeyCredential(key)) as search_index_client:
            search_index_client.delete_index(index_name)
            print(f"Index {index_name} deleted")

    except Exception as ex:
        print(ex)

def _create_index():

    try:
        fields = [
            SimpleField(name="id", type=SearchFieldDataType, key=True, filterable=True, facetable=True),
            SearchableField(name="title", type=SearchFieldDataType.String),
            SearchableField(name="content", type=SearchFieldDataType.String),
            SearchableField(name="category", type=SearchFieldDataType.String, filterable=True),
            SearchField(name="titleVector", type=SearchFieldDataType.Collection(SearchFieldDataType.Single), searchable=True, hidden=False, vector_search_dimensions=1536, vector_search_profile_name="myHnswProfile"),
            SearchField(name="contentVector", type=SearchFieldDataType.Collection(SearchFieldDataType.Single), searchable=True, hidden=False, vector_search_dimensions=1536, vector_search_profile_name="myHnswProfile")
        ]


        vector_search = VectorSearch(
            algorithms=[
                HnswAlgorithmConfiguration(name="myHnsw")
            ],
            profiles=[
                VectorSearchProfile(
                    name="myHnswProfile",
                    algorithm_configuration_name="myHnsw",
                    vectorizer="myVectorizer"
                )
            ],
            vectorizers=[
                AzureOpenAIVectorizer(
                    name="myVectorizer",
                    azure_open_ai_parameters=AzureOpenAIParameters(
                        resource_uri=azure_openai_endpoint,
                        deployment_id=azure_openai_embedding_deployment,
                        model_name=azure_openai_embedding_deployment,
                        api_key=azure_openai_model
                    )
                )
            ]
        )

        scoring_profiles:List[ScoringProfile] = []
        scoring_profile = ScoringProfile(name="MyProfile", text_weights=TextWeights(weights={"title":1.5}))
        scoring_profiles.append(scoring_profile)
        cors_options = CorsOptions(allowed_origins=["*"], max_age_in_seconds=60)

        semantic_config = SemanticConfiguration(
            name="my-semantic-config",
            prioritized_fields=SemanticPrioritizedFields(
                title_field=SemanticField(field_name="title"),
                keywords_fields=[SemanticField(field_name="category")],
                content_fields=[SemanticField(field_name="content")]
            )
        )

        semantic_search = SemanticSearch(configurations=[semantic_config])

        index = SearchIndex(
            name=index_name,
            fields=fields,
            cors_options=cors_options,
            vector_search=vector_search,
            smeantic_search=semantic_search
        )

        with SearchIndexClient(service_endpoint, AzureKeyCredential(key)) as search_index_client:
            result = search_index_client.create_index(index)
            print(f"Index {index_name} created.")
    except Exception as ex:
        print(ex)

def _create_data_source():

    try:
        container = SearchIndexerDataContainer(name="azure_services_vector_container")

        data_source_connection = SearchIndexerDataSourceConnection(
            name=data_source_name,
            type="azureblob",
            connection_string=connection_string,
            container=container
        )

        with SearchIndexerClient(service_endpoint, AzureKeyCredential(key)) as search_indexer_client:
            search_indexer_client.create_data_source_connection(data_source_connection)
            print(f"Data source {data_source_name} created.")

    except Exception as ex:
        print(ex)

def _export_embeddings_to_json():

    try:
        path = os.path.join("..","JsonFile","text-sample.json")
        with open(path,"r",encoding="utf-8") as file:
            input_data = json.load(file)

        titles = [item['title'] for item in input_data]
        contents = [item['content'] for item in input_data]
        title_response = openai.embeddings.create(input=titles, model=azure_openai_embedding_deployment, dimensions=1536)
        title_embeddings = [item.embedding for item in title_response.data]
        content_response = openai.embeddings.create(input=contents, model=azure_openai_embedding_deployment, dimensions=1536)
        content_embeddings = [item.embedding for item in content_response.data]

        for i,item in enumerate(input_data):
            title = item['title']
            content = item['content']
            item['titleVector'] = title_embeddings[i]
            item['contentVector'] = content_embeddings[i]

        output_path = os.path.join("..","JsonFile","text-sample-embeddings2.json")
        output_directory = os.path.dirname(output_path)
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
        with open(output_path,"w",encoding="utf-8") as file:
            json.dump(input_data, file, indent=4, ensure_ascii=False)
    except Exception as ex:
        print(ex)

if __name__ == "__main__":
    _export_embeddings_to_json()

