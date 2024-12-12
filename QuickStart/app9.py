# azure-search-documents==11.5.2
import os,json,logging,sys
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import QueryType, QueryCaptionType, QueryAnswerType, QueryCaptionResult, QueryAnswerResult, VectorizableTextQuery
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
index_name = "manual-vector-index"
manual_skillset_name = "manual-skillset"

azure_openai_model = "gpt-4o"
azure_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
azure_openai_key = os.getenv("OPENAI_API_KEY")
azure_openai_embedding_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_FOR_EMBEDDINGS")
azure_openai_api_version = os.getenv("OPENAI_API_VERSION")


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
                SearchField(name="parent_id", type=SearchFieldDataType.String),  
                SearchField(name="title", type=SearchFieldDataType.String),
                SearchField(name="chunk_id", type=SearchFieldDataType.String, key=True, sortable=True, filterable=True, facetable=True, analyzer_name="keyword"),  
                SearchField(name="chunk", type=SearchFieldDataType.String, sortable=False, filterable=False, facetable=False),  
                SearchField(name="text_vector", type=SearchFieldDataType.Collection(SearchFieldDataType.Single), vector_search_dimensions=1024, vector_search_profile_name="myHnswProfile")
        ] 

        vector_search = VectorSearch(
            algorithms=[
                HnswAlgorithmConfiguration(name="myHnsw")
            ],
            profiles=[
                VectorSearchProfile(
                    name="myHnswProfile",
                    algorithm_configuration_name="myHnsw",
                    vectorizer_name="myVectorizer"
                )
            ],
            vectorizers=[
                AzureOpenAIVectorizer(
                    vectorizer_name="myVectorizer",
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
        
        with SearchIndexClient(service_endpoint, AzureKeyCredential(key)) as search_index_client:
            result = search_index_client.create_index(index)
            print(f"{result.name} created")
    except Exception as ex:
        print(ex)

def _create_datasource():

    container = SearchIndexerDataContainer(name="manual")
    data_source_connection = SearchIndexerDataSourceConnection(
        name="manual-datasource",
        type="azureblob",
        connection_string=os.getenv("AZURE_STORAGE_CONNECTION_STRING"),
        container=container
    )

    with SearchIndexerClient(service_endpoint, AzureKeyCredential(key)) as search_indexer_client:
        data_source = search_indexer_client.create_data_source_connection(data_source_connection)
        print(f"Data source '{data_source.name}' created")

def _create_skillset():

    try:
        split_skill = SplitSkill(
            description="Split Skill to chunk documents",
            text_split_mode="pages",
            context="/document",
            maximum_page_length=2000,
            page_overlap_length=500,
            inputs=[
                InputFieldMappingEntry(name="text", source="/document/content")
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

        index_projections = SearchIndexerIndexProjection(
        selectors=[
            SearchIndexerIndexProjectionSelector(
                target_index_name=index_name,
                parent_key_field_name="parent_id",
                source_context="/document/pages/*",
                mappings=[
                    InputFieldMappingEntry(name="chunk", source="/document/pages/*"),
                    InputFieldMappingEntry(name="text_vector", source="/document/pages/*/text_vector"),
                    InputFieldMappingEntry(name="title", source="/document/metadata_storage_name")
                ]
            )
        ],
        parameters=SearchIndexerIndexProjectionsParameters(
            projection_mode=IndexProjectionMode.SKIP_INDEXING_PARENT_DOCUMENTS
        )
    )

        

        skillset = SearchIndexerSkillset(
            name="manual-skillset",
            skills=[split_skill,embedding_skill],
            description="Skillset to split and embed documents",
            index_projection=index_projections
        )

        with SearchIndexerClient(service_endpoint, AzureKeyCredential(key)) as search_indexer_client:
            result = search_indexer_client.create_skillset(skillset)
            print(f"Skillset '{result.name}' created")
    except Exception as ex:
        print(ex)

def _create_indexer():

    try:

        indexer = SearchIndexer(
            name=index_name,
            description="Indexer to index manual documents",
            skillset_name=manual_skillset_name,
            target_index_name=index_name,
            data_source_name="manual-datasource",
            parameters=None,
            # field_mappings=[FieldMapping(source_field_name="metadata_storage_name", target_field_name="title")],
            # output_field_mappings=[
            #     FieldMapping(source_field_name="/document/pages/*/text", target_field_name="chunk"),
            #     # FieldMapping(source_field_name="/document/pages/*/text_vector", target_field_name="text_vector")
            # ]
        )

        with SearchIndexerClient(service_endpoint, AzureKeyCredential(key)) as search_indexer_client:
            result = search_indexer_client.create_indexer(indexer)
            print(f"Indexer '{result.name}' created" )
    except Exception as ex:
        print(ex)

def query():

    query = "學生事務處職涯發展組電話是多少?"

    with SearchClient(service_endpoint, index_name, AzureKeyCredential(key)) as search_client:
        vector_query = VectorizableTextQuery(text=query, k_nearest_neighbors=1, fields="text_vector")

        results = search_client.search(
            search_text="query",
            vector_queries=[vector_query],
            select=["chunk"],
            top=1
        )

        for result in results:
            print(f"Score: {result['@search.score']}")
            print(f"Chunk: {result['chunk']}")




if __name__ == "__main__":
    # _create_index()
    # _create_datasource()
    # _create_skillset()
    # _create_indexer()
    query()