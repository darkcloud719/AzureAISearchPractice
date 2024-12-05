import os,json,logging,sys
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import QueryType, QueryCaptionResult, QueryAnswerResult
from azure.search.documents.indexes import SearchIndexClient, SearchIndexerClient
from azure.search.documents.indexes.models import(
    SearchIndexerDataContainer,
    SearchIndex,
    SimpleField,
    SearchFieldDataType,
    EntityRecognitionSkill,
    EntityRecognitionSkillVersion,
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
from rich import print as pprint

load_dotenv()

service_endpoint = os.getenv("AZURE_SEARCH_SERVICE_ENDPOINT")
key = os.getenv("AZURE_SEARCH_API_KEY")
index_name = "hotel-quickstart2"
indexer_name = "hotel-quickstart2-indexer"
connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")

search_client = SearchClient(service_endpoint, index_name, AzureKeyCredential(key))
search_index_client = SearchIndexClient(service_endpoint, AzureKeyCredential(key))
search_indexer_client = SearchIndexerClient(service_endpoint, AzureKeyCredential(key))

def _delete_index():

    try:
        resutl = search_index_client.delete_index(index_name)
        print(f"Index {index_name} deleted")
    except Exception as ex:
        print(ex)

def _get_index():
    
    try:
        result = search_index_client.get_index(index_name)
        print(f"Index {index_name} found")
    except Exception as ex:
        print(ex)

def _create_index():

    try:
        fields = [
            SimpleField(name="hotelId", type=SearchFieldDataType.String, key=True, filterable=True, sortable=True),
            SimpleField(name="hotelName", type=SearchFieldDataType.String, sortable=True),
            SearchableField(name="description", type=SearchFieldDataType.String, analyzer_name="en.lucene"),
            SearchableField(name="descriptionFr", type=SearchFieldDataType.String, analyzer_name="fr.lucene"),
            SearchableField(name="category", type=SearchFieldDataType.String, facetable=True, filterable=True, sortable=True),
            SearchableField(name="tags", type=SearchFieldDataType.String, facetable=True, filterable=True, collection=True),
            SimpleField(name="parkingIncluded", type=SearchFieldDataType.Boolean, facetable=True, filterable=True, sortable=True),
            SimpleField(name="smokingAllowed", type=SearchFieldDataType.Boolean, facetable=True, filterable=True, sortable=True),
            SimpleField(name="lastRenovationDate", type=SearchFieldDataType.DateTimeOffset, facetable=True, filterable=True, sortable=True),
            SimpleField(name="rating", type=SearchFieldDataType.Double, facetable=True, filterable=True, sortable=True),
            SimpleField(name="location", type=SearchFieldDataType.GeographyPoint),
            ComplexField(name="address", fields=[
                SearchableField(name="streetAddress", type=SearchFieldDataType.String),
                SearchableField(name="city", type=SearchFieldDataType.String),
                SearchableField(name="stateProvince", type=SearchFieldDataType.String, facetable=True, filterable=True, sortable=True),
                SearchableField(name="postalCode", type=SearchFieldDataType.String, facetable=True, filterable=True, sortable=True),
                SearchableField(name="country", type=SearchFieldDataType.String, facetable=True, filterable=True, sortable=True)
            ]),
            SimpleField(name="url", type=SearchFieldDataType.String),
            SimpleField(name="file_name", type=SearchFieldDataType.String),
            SearchableField(name="emails", type=SearchFieldDataType.String, colleciton=True),
            SimpleField(name="mysentiment", type=SearchFieldDataType.String),
            ComplexField(
                name="namedEntities",
                fields=[
                    SimpleField(name="text", type=SearchFieldDataType.String),
                    SimpleField(name="category", type=SearchFieldDataType.String),
                    SimpleField(name="subcategory", type=SearchFieldDataType.String),
                    SimpleField(name="length", type=SearchFieldDataType.Int32),
                    SimpleField(name="offset", type=SearchFieldDataType.Int32),
                    SimpleField(name="confidenceScore", type=SearchFieldDataType.Double)
                ],
                collection=True
            ),
        ]

        semantic_config = SemanticConfiguration(
            name="my-semantic-config",
            prioritized_fields=SemanticPrioritizedFields(
                title_field=SemanticField(field_name="hotelName"),
                keywords_fields=[SemanticField(field_name="category")],
                content_fields=[SemanticField(field_name="description")]
            )
        )

        semantic_search = SemanticSearch(configurations=[semantic_config])

        scoring_profiles:List[ScoringProfile] = []
        scoring_profile = ScoringProfile(
            name="MyProfile",
            text_weights=TextWeights(weights={"description":1.5}),
        )
        scoring_profiles.append(scoring_profile)
        cors_options = CorsOptions(allowed_origins=["*"], max_age_in_seconds=60)
        suggester = [{'name':'sg','source_fields':['tags','address/city','address/country']}]

        index = SearchIndex(
            name=index_name,
            fields=fields,
            scoring_profiles=scoring_profiles,
            cors_options=cors_options,
            suggesters=suggester,
            semantic_search=semantic_search
        )

        result = search_index_client.create_index(index)

        return result
    
    except Exception as ex:
        logging.error(ex)

def _create_data_source():

    container = SearchIndexerDataContainer(name="searchcontainer")

    data_source_connection = SearchIndexerDataSourceConnection(
        name="hotel-quickstart-datasource",
        type="azureblob",
        connection_string=connection_string,
        container=container
    )

    data_source = search_indexer_client.create_data_source_connection(data_source_connection)

    return data_source

def _create_skillset():
    search_indexer_client.delete_skillset("hotel-quickstart-skillset")
    
    inp = InputFieldMappingEntry(name="text", source="/document/description")
    sentiment_output = OutputFieldMappingEntry(name="sentiment", target_name="mysentiment")
    email_output = OutputFieldMappingEntry(name="emails", target_name="emails")
    name_output = OutputFieldMappingEntry(name="namedEntities", target_name="namedEntities")
    
    sentimentSkill = SentimentSkill(name="my-sentiment-skill", inputs=[inp], outputs=[sentiment_output])
    entityRecognitionSkill = EntityRecognitionSkill(name="entity-recognition-skill", inputs=[inp], outputs=[email_output, name_output])
    skillset = SearchIndexerSkillset(
        name="hotel-quickstart-skillset",
        skills=[sentimentSkill, entityRecognitionSkill],
        description="Sentiment and Entity Recognition Skillset"
    )
    result = search_indexer_client.create_skillset(skillset)

    return result

def sample_indexer_workflow():

    _delete_index()

    skillset_name = _create_skillset().name
    print(f"{skillset_name} is created")

    datasource = _create_data_source().name
    print(f"{datasource} is created")

    ind_name = _create_index().name
    print(f"{ind_name} is created")

    configuration = IndexingParametersConfiguration(
        parsing_mode="jsonArray",
        query_timeout=None
    )

    parameters = IndexingParameters(configuration=configuration)

    indexer = SearchIndexer(
        name=indexer_name,
        data_source_name=datasource,
        target_index_name=ind_name,
        skillset_name=skillset_name,
        parameters=parameters,
        field_mappings=[
            FieldMapping(source_field_name="hotelName", target_field_name="hotelName"),
            FieldMapping(source_field_name="metadata_storage_path", target_field_name="url"),
            FieldMapping(source_field_name="metadata_storage_name", target_field_name="file_name")
        ],
        output_field_mappings=[
            FieldMapping(source_field_name="/document/mysentiment", target_field_name="mysentiment"),
            FieldMapping(source_field_name="/document/emails", target_field_name="emails"),
            FieldMapping(source_field_name="/document/namedEntities", target_field_name="namedEntities")
        ]
    )

    search_indexer_client.create_indexer(indexer)

    result = search_indexer_client.get_indexer(indexer_name)

    print(f"Indexer {result.name} created")

    search_indexer_client.run_indexer(indexer_name)

    print(f"Indexer {result.name} is running")


if __name__ == "__main__":

    sample_indexer_workflow()    
