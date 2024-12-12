# azure-search-documents==11.5.2
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
    SemanticConfiguration,
    SemanticField,
    SemanticPrioritizedFields,
    SemanticSearch,
    SearchField,
    VectorSearch,
    VectorSearchAlgorithmConfiguration,
    VectorSearchProfile,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
    AzureOpenAIVectorizer,
    AzureOpenAIVectorizerParameters,
    SplitSkill,
    AzureOpenAIEmbeddingSkill,
    SearchIndexerIndexProjection,
    SearchIndexerIndexProjectionSelector,
    SearchIndexerIndexProjectionsParameters,
    IndexProjectionMode,
    SearchIndexerSkillset,
    CognitiveServicesAccountKey
)
from dotenv import load_dotenv
from typing import List

load_dotenv()

service_endpoint = os.getenv("AZURE_SEARCH_SERVICE_ENDPOINT")
key = os.getenv("AZURE_SEARCH_API_KEY")
index_name = "py-rag-tutorial-idx"

azure_openai_model = "gpt-4o"
azure_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
azure_openai_key = os.getenv("OPENAI_API_KEY")
azure_openai_embedding_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_FOR_EMBEDDINGS")
azure_openai_api_version = os.getenv("OPENAI_API_VERSION")

search_client = SearchClient(service_endpoint, index_name, AzureKeyCredential(key))
search_index_client = SearchIndexClient(service_endpoint, AzureKeyCredential(key))
search_indexer_client = SearchIndexerClient(service_endpoint, AzureKeyCredential(key))
sb_connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")

# 
def delete_index():

    search_index_client.delete_index(index_name)

def create_index():

    fields = [
        SearchableField(name="parent_id", type=SearchFieldDataType.String, filterable=True),
        SearchableField(name="title", type=SearchFieldDataType.String),
        SearchableField(name="locations", type=SearchFieldDataType.String, filterable=True, collection=True),
        SearchableField(name="chunk_id", type=SearchFieldDataType.String, key=True, sortable=True, filterable=True, facetable=True, analyzer_name="keyword"),
        SearchableField(name="chunk", type=SearchFieldDataType.String),
        SearchField(name="text_vector", type=SearchFieldDataType.Collection(SearchFieldDataType.Single), vector_search_dimensions=1024, vector_search_profile_name="myHnswProfile")
    ]

    vector_search = VectorSearch(
        algorithms=[
            HnswAlgorithmConfiguration(name="myHnsw"),
        ],
        profiles=[
            VectorSearchProfile(
                name="myHnswProfile",
                algorithm_configuration_name="myHnsw",
                vectorizer_name="myOpenAI"
            )
        ],
        vectorizers=[
            AzureOpenAIVectorizer(
                vectorizer_name="myOpenAI",
                kind="azureOpenAI",
                parameters=AzureOpenAIVectorizerParameters(
                    resource_url=azure_openai_endpoint,
                    deployment_name="text-embedding-3-large",
                    model_name="text-embedding-3-large",
                    api_key=azure_openai_key
                )
            )
        ]

    )

    index = SearchIndex(
        name=index_name,
        fields=fields,
        vector_search=vector_search
    )
    result = search_index_client.create_or_update_index(index)
    print(f"{result.name} created")

def create_datasource():

    container = SearchIndexerDataContainer(name="nasa-ebooks-pdfs-all")
    data_source_connection = SearchIndexerDataSourceConnection(
        name="py-rag-tutorial-ds",
        type="azureblob",
        connection_string=sb_connection_string,
        container=container
    )
    data_source = search_indexer_client.create_or_update_data_source_connection(data_source_connection)

    print(f"Data source '{data_source.name}' created  or updated")

def create_skillset():

    skillset_name = "py-rag-tutorial-ss"

    split_skill = SplitSkill(
        description="Split skill to chunk documents",
        text_split_mode="pages",
        context="/document",
        maximum_page_length=2000,
        page_overlap_length=500,
        inputs=[
            InputFieldMappingEntry(name="text", source="/document/content"),
        ],
        outputs=[
            OutputFieldMappingEntry(name="textItems", target_name="pages")
        ]
    )

    embedding_skill = AzureOpenAIEmbeddingSkill(
        description="Skill to generate embeddings via Azure OpenAI",
        context="/document/pages/*",
        resource_url=azure_openai_endpoint,
        deployment_name="text-embedding-3-large",
        model_name="text-embedding-3-large",
        dimensions=1024,
        api_key=azure_openai_key,
        inputs=[
            InputFieldMappingEntry(name="text", source="/document/pages/*")
        ],
        outputs=[
            OutputFieldMappingEntry(name="embedding", target_name="text_vector")
        ]
    )

    entity_skill = EntityRecognitionSkill(
        description="Skill to recognitze entities in text",
        context="/document/pages/*",
        categories=["Location"],
        default_language_code="en",
        inputs=[
            InputFieldMappingEntry(name="text", source="/document/pages/*")
        ],
        outputs=[
            OutputFieldMappingEntry(name="locations", target_name="locations")
        ]
    )

    index_projections = SearchIndexerIndexProjection(
        selectors=[
            SearchIndexerIndexProjectionSelector(
                target_index_name=index_name,
                parent_key_field_name="parent_id",
                source_context="/document/pages/*",
                mappings=[
                    InputFieldMappingEntry(name="chunk", source="/document/pages/*"),
                    InputFieldMappingEntry(name="text_vector", source="/document/pages/*/text_vector"),
                    InputFieldMappingEntry(name="locations", source="/document/pages/*/locations"),
                    InputFieldMappingEntry(name="title", source="/document/metadata_storage_name")
                ]
            )
        ],
        parameters=SearchIndexerIndexProjectionsParameters(
            projection_mode=IndexProjectionMode.SKIP_INDEXING_PARENT_DOCUMENTS
        )
    )

    skills = [split_skill,embedding_skill,entity_skill]

    skillset = SearchIndexerSkillset(
        name=skillset_name,
        description="Skillset to chunk documents and generating embeddings",
        skills=skills,
        index_projection=index_projections,
    )

    search_indexer_client.create_or_update_skillset(skillset)
    print(f"{skillset.name} created")

def create_indexer():

    indexer_name = "py-rag-tutorial-idxr"
    skillset_name = "py-rag-tutorial-ss"
    data_source_name = "py-rag-tutorial-ds"

    indexer_parameters = None
    
    indexer = SearchIndexer(
        name=indexer_name,
        description="Indexer to index documents and generate embeddings",
        skillset_name=skillset_name,
        target_index_name=index_name,
        data_source_name=data_source_name,
        parameters=indexer_parameters
    )

    # Create the indexer
    indexer_result = search_indexer_client.create_or_update_indexer(indexer)

    print(f"{indexer_name} is created and running. Give the indexer a few minutes before running a query.")

def run_a_query():

    query = "The Meeting of the Waters"

    results = search_client.search(
        search_text=query,
        select=["chunk"],
        top=1
    )

    for result in results:
        print(f"Score: {result['@search.score']}")
        print(f"Chunk: {result['chunk']}")

def search_using_a_chat_model():

    GROUNDED_PROMPT = """

    """


if __name__ == "__main__":
    # delete_index()
    # create_index()
    # create_datasource()
    # create_skillset()
    # create_indexer()
    run_a_query()