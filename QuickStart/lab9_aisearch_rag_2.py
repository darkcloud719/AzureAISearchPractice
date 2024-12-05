import os,json,logging,sys,openai
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
index_name = "hotels-sample-index"

openai.api_key = os.getenv("OPENAI_API_KEY")
openai.azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
openai.api_version = os.getenv("OPENAI_API_VERSION")
openai.api_type = "azure"

search_client = SearchClient(service_endpoint, index_name, AzureKeyCredential(key))
search_index_client = SearchIndexClient(service_endpoint, AzureKeyCredential(key))

def update_index():

    try:
        semantic_config = SemanticConfiguration(
            name="my-semantic-config",
            prioritized_fields=SemanticPrioritizedFields(
                title_field=SemanticField(field_name="HotelName"),
                keywords_fields=[SemanticField(field_name="Tags")],
                content_fields=[SemanticField(field_name="Description")]
            )
        )

        semantic_search = SemanticSearch(configurations=[semantic_config])

        scoring_profiles:List[ScoringProfile] = []
        scoring_profile = ScoringProfile(
            name="MyProfile",
            text_weights=TextWeights(weights={"Description":1.2})
        )
        scoring_profiles.append(scoring_profile)

        index = search_index_client.get_index(index_name)
        index.scoring_profiles = scoring_profiles
        index.semantic_search = semantic_search

        result = search_index_client.create_or_update_index(index)
        print(f"Index {index_name} updated.")
    except Exception as ex:
        print(ex)

def main():

    GROUNDED_PROMPT="""
    You are a friendly assistant that recommends hotels based on activities and amenities.
    Answer the query using only the sources provided below in a friendly and concise bulleted manner.
    Answer ONLY with the facts listed in the list of sources below.
    If there isn't enough information below, say you don't know.
    Do not generate answers that don't use the sources below.
    Query: {query}
    Sources:\n{sources}
    """

    query = "Can you recommend a few hotels that offer complimentary breakfast? Tell me their description, address, tags, and the rate for one room they have which sleep 4 people."

    # Set up the search results and the chat thread.
    # Retrieve the selected fields from the search index related to the question.
    selected_fields = ["HotelName","Description","Address","Rooms","Tags"]
    search_results = search_client.search(
        search_text=query,
        top=5,
        select=selected_fields,
        query_type=QueryType.SEMANTIC,
        semantic_configuration_name="my-semantic-config"
    )
    sources_filtered = [{field: result[field] for field in selected_fields} for result in search_results]
    sources_formatted = "\n".join([json.dumps(source)for source in sources_filtered])

    # print(GROUNDED_PROMPT.format(query=query, sources=sources_formatted))

    response = openai.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        messages=[
            {
                "role":"user",
                "content":GROUNDED_PROMPT.format(query=query, sources=sources_formatted)
            }
        ]
    )

    print(response.choices[0].message.content)

if __name__ == "__main__":
    # update_index()
    main()