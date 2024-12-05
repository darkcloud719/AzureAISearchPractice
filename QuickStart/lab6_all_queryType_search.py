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
index_name = "azure-services"

def search_index_by_queryType_simple():

    try:
        with SearchClient(service_endpoint, index_name, AzureKeyCredential(key)) as search_client:
            results = search_client.search(
                query_type=QueryType.SIMPLE,
                search_text="gateway",
                # search_text="wifi -parking"
                # search_text="wifi +parking"
                # search_text="'free wifi'"
                include_total_count=True
            )

            for result in results:
                for result_key, value in result.items():
                    print(f"{result_key}:{value}")

                print("\n\n")

    except Exception as ex:
        print(ex)

def search_index_by_queryType_full():

    try:
        with SearchClient(service_endpoint, index_name, AzureKeyCredential(key)) as search_client:
            results = search_client.search(
                query_type=QueryType.FULL,
                search_text="gateway",
                # search_text="gateway AND networking",
                # search_text="gateway OR networking",
                # search_text="gateway AND NOT networking",
                # search_text="title:gateway",
                # search_text="rating:[4 TO 5]",
                # search_text="gateway AND (networking OR security)"
                include_total_count=True,
                top=2
            )

            for result in results:
                for result_key, value in result.items():
                    print(f"{result_key}:{value}")
                print("\n\n")

    except Exception as ex:
        print(ex)

def _update_index():

    try:
        semantic_config = SemanticConfiguration(
            name="my-semantic-config",
            prioritized_fields=SemanticPrioritizedFields(
                title_field=SemanticField(field_name="title"),
                keywords_fields=[SemanticField(field_name="category")],
                content_fields=[SemanticField(field_name="content")]
            )
        )

        semantic_search = SemanticSearch(configurations=[semantic_config])

        with SearchIndexClient(service_endpoint, AzureKeyCredential(key)) as search_index_client:
            index = search_index_client.get_index(index_name)
            index.semantic_search = semantic_search
            result = search_index_client.create_or_update_index(index)
            print(f"Index {index_name} updated")
    except Exception as ex:
        logging.error(ex)

def search_index_by_queryType_semantic():

    try:
        with SearchClient(service_endpoint, index_name, AzureKeyCredential(key)) as search_client:
            results = search_client.search(
                query_type=QueryType.SEMANTIC,
                search_text="gateway",
                include_total_count=True,
                # required
                semantic_configuration_name="my-semantic-config",
                query_caption="extractive",
                query_answer="extractive"
            )

            print(f"Total count: {results.get_count()}")

            for result in results:
                for result_key, value in result.items():
                    print(f"{result_key}:{value}")
                print("\n\n")

                captions = result["@search.captions"]

                if captions:
                    caption = captions[0]
                    if caption.highlights:
                        print(f"Caption highlights:{caption.highlights}\n")
                    else:
                        print(f"Caption text:{caption.text}\n")
                print("\n\n")
            
            semantic_answers = results.get_answers()
            print("<answers start>\n")
            for answer in semantic_answers:
                if answer.highlights:
                    print(f"Semantic Answer highlights:{answer.highlights}")
                else:
                    print(f"Semantic Answer text:{answer.text}")
            print("<answers end>\n")
    except Exception as ex:
        print(ex)



if __name__ == "__main__":
    # search_index_by_queryType_simple()
    # search_index_by_queryType_full()
    _update_index()
    search_index_by_queryType_semantic()

