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

search_client = SearchClient(service_endpoint, index_name, AzureKeyCredential(key))
search_index_client = SearchIndexClient(service_endpoint, AzureKeyCredential(key))
search_indexer_client = SearchIndexerClient(service_endpoint, AzureKeyCredential(key))

def _run_first_query():

    try:
        results = search_client.search(
            query_type=QueryType.SIMPLE,
            search_text="*",
            select="hotelName,description",
            include_total_count=True
        )

        print(f"Total Documents Matching Querying: {results.get_count()}")

        for result in results:
            for key,value in result.items():
                print(f"{key}:{value}")
            print("\n")
    except Exception as ex:
        print(ex)

def _run_a_term_query():
    try:
        results = search_client.search(
            query_type=QueryType.SIMPLE,
            search_text="24 hours hotel",
            select="hotelName,description",
            search_fields=["tags","description"],
            scoring_profile="MyProfile",
            include_total_count=True
        )
        print(f"Total Documents Matching Querying: {results.get_count()}")
        for result in results:
            for key,value in result.items():
                print(f"{key}:{value}")
            print("\n")
    except Exception as ex:
        print(ex)

def _run_a_filter_query():

    try:
        results = search_client.search(
            query_type=QueryType.SIMPLE,
            search_text="hotels",
            select="hotelId,hotelName,rating",
            filter="rating gt 4",
            order_by=["rating desc"]
        )

        for result in results:
            for key,value in result.items():
                print(f"{key}:{value}")
            print("\n")
    except Exception as ex:
        print(ex)

def _run_look_up_document():

    try:
        result = search_client.get_document(key="3")

        for key,value in result.items():
            print(f"{key}:{value}")
    except Exception as ex:
        print(ex)

def _run_a_suggest_query():

    try:
        search_suggestion = "sa"
        results = search_client.autocomplete(
            search_text=search_suggestion,
            suggester_name="sg",
            mode="twoTerms"
        )

        print(f"Autocomplete Suggestions: {search_suggestion}")

        for result in results:
            for key,value in result.items():
                print(f"{key}:{value}")
            print("\n")
    except Exception as ex:
        print(ex)


if __name__ == "__main__":
    # _run_first_query()
    # _run_a_term_query()
    # _run_a_filter_query()
    # _run_look_up_document()
    _run_a_suggest_query()
