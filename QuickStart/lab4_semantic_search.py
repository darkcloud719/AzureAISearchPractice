import os,json,logging,sys
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import QueryType, QueryCaptionResult, QueryAnswerResult, QueryCaptionType, QueryAnswerType
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
            text_weights=TextWeights(weights={"tags":2,"description":1}),
        ) 
        scoring_profiles.append(scoring_profile)

        index = search_index_client.get_index(index_name)
        index.scoring_profiles = scoring_profiles
        index.semantic_search = semantic_search

        result = search_index_client.create_or_update_index(index)
        print(f"Index {index_name} updated")

    except Exception as ex:
        print(ex)

def _run_semantic_queries():
    
    try:
        results = search_client.search(
            query_type="semantic",
            semantic_configuration_name="my-semantic-config",
            search_text="What hotel has a good restaurant on site?",
            select="hotelName,description,category",
            query_caption="extractive"
        )

        for result in results:
            for key,value in result.items():
                print(f"{key}:{value}")
            print("\n")

            captions = result["@search.captions"]

            if captions:
                caption = captions[0]
                if caption.highlights:
                    print(f"Caption highlights:{caption.highlights}\n")
                else:
                    print(f"Caption text:{caption.text}\n")
            print("\n\n")
    except Exception as ex:
        print(ex)

def _run_semantic_answers():

    try:
        results = search_client.search(
            query_type="semantic",
            semantic_configuration_name="my-semantic-config",
            search_text="What hotel is in a historic building?",
            select="hotelName,description,category",
            query_caption="extractive",
            query_answer="extractive"
        )

        for result in results:
            for key,value in result.items():
                print(f"{key}:{value}")
            print("\n")

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
    # _update_index()
    # _run_semantic_queries()
    _run_semantic_answers()

    