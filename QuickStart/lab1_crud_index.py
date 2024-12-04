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
index_name = "hotels-quickstart"


search_client = SearchClient(endpoint=service_endpoint, index_name=index_name, credential=AzureKeyCredential(key))
search_index_client = SearchIndexClient(endpoint=service_endpoint, credential=AzureKeyCredential(key))
search_indexer_client = SearchIndexerClient(endpoint=service_endpoint, credential=AzureKeyCredential(key))

def _get_index():
    try:
        result = search_index_client.get_index(index_name)
        print(f"Index {index_name} exists")
    except Exception as ex:
        print(ex)

def _delete_index():
    try:
        search_index_client.delete_index(index_name)
        print(f"Index {index_name} deleted")
    except Exception as ex:
        print(ex)

def _create_index():
    try:
        fields = [
            SimpleField(name="hotelId", type=SearchFieldDataType.String, key=True),
            SearchableField(name="hotelName", type=SearchFieldDataType.String, sortable=True),
            SearchableField(name="description", type=SearchFieldDataType.String, analyzer_name="en.lucene"),
            SearchableField(name="description_fr", type=SearchFieldDataType.String, analyzer_name="fr.lucene"),
            SearchableField(name="category", type=SearchFieldDataType.String, facetable=True, filterable=True, sortable=True),
            SearchableField(name="tags", type=SearchFieldDataType.String, facetable=True, filterable=True, collection=True),
            SimpleField(name="parkingIncluded", type=SearchFieldDataType.Boolean, facetable=True, filterable=True, sortable=True),
            SimpleField(name="lastRenovationDate", type=SearchFieldDataType.DateTimeOffset, facetable=True, filterable=True, sortable=True),
            SimpleField(name="rating", type=SearchFieldDataType.Double, facetable=True, filterable=True, sortable=True),
            ComplexField(name="address", fields=[
                SearchableField(name="streetAddress", type=SearchFieldDataType.String),
                SearchableField(name="city", type=SearchFieldDataType.String),
                SearchableField(name="stateProvince", type=SearchFieldDataType.String, facetable=True, filterable=True, sortable=True),
                SearchableField(name="postalCode", type=SearchFieldDataType.String, facetable=True, filterable=True, sortable=True),
                SearchableField(name="country", type=SearchFieldDataType.String, facetable=True, filterable=True, sortable=True)
            ])
        ]

        scoring_profiles:List[ScoringProfile] = []
        scoring_profile = ScoringProfile(
            name="MyProfile",
            text_weights=TextWeights(weights={"description":1.5})
        )
        scoring_profiles.append(scoring_profile)
        cors_options = CorsOptions(allowed_origins=["*"], max_age_in_seconds=60)
        suggester = [{'name':'sg','source_fields':['tags','address/city','address/country']}]

        index = SearchIndex(
            name=index_name,
            fields=fields,
            scoring_profiles=scoring_profiles,
            cors_options=cors_options,
            suggesters=suggester
        )

        result = search_index_client.create_index(index)
        print(f"Index {index_name} created")
    except Exception as ex:
        print(ex)

def _update_index():
    try:
        semantic_config = SemanticConfiguration(
            name="my-semantic-config",
            prioritized_fields=SemanticPrioritizedFields(
                title_field=SemanticField(field_name="hotelName"),
                keywords_fields=[SemanticField(field_name="tags")],
                content_fields=[SemanticField(field_name="description")]
            )
        )

        semantic_search = SemanticSearch(configurations=[semantic_config])

        scoring_profiles:List[ScoringProfile] = []
        scoring_profile = ScoringProfile(
            name="MyProfile",
            text_weights=TextWeights(weights={"description":1.2}),
        )
        scoring_profiles.append(scoring_profile)

        index = search_index_client.get_index(index_name)
        index.scoring_profiles = scoring_profiles
        index.semantic_search = semantic_search

        result = search_index_client.create_or_update_index(index)
        print(f"Index {index_name} updated.")
    except Exception as ex:
        print(ex)



if __name__ == "__main__":
    # _get_index()
    # _delete_index()
    # _create_index()
    _update_index()
