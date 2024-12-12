# azure-search-documents==11.5.2
import os,json,logging,sys,openai
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

openai.api_key = os.getenv("OPENAI_API_KEY")
openai.azure_endpoint =os.getenv("AZURE_OPENAI_ENDPOINT")
openai.api_version = os.getenv("OPENAI_API_VERSION")
openai.api_type = "azure"


def query_assistant():
    GROUNDED_PROMPT="""
    You are an AI assistant that helps users learn from the information found in the source material.
    Answer the query using only the sources provided below.
    Use bullets if the answer has multiple points.
    If the answer is longer than 3 sentences, provide a summary.
    Answer ONLY with the facts listed in the list of sources below. Cite your source when you answer the question
    If there isn't enough information below, say you don't know.
    Do not generate answers that don't use the sources below.
    Query: {query}
    Sources:\n{sources}
    """

    # query = "學生事務處職涯發展組電話是多少?"
    query = "文化大學諮商中心電話是多少?"
    vector_query = VectorizableTextQuery(text=query, k_nearest_neighbors=2, fields="text_vector")

    with SearchClient(service_endpoint, index_name, AzureKeyCredential(key)) as search_client:
        results = search_client.search(
            search_text="query",
            vector_queries=[vector_query],
            select=["title","chunk"],
            top=2
        )

        sources_formatted = "=================\n".join([f'TITLE: {document["title"]}, CONTENT: {document["chunk"]}' for document in results])  

        print(GROUNDED_PROMPT.format(query=query, sources=sources_formatted))

        
        response = openai.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            messages=[
                {
                    "role":"user",
                    "content":GROUNDED_PROMPT.format(query=query, sources=sources_formatted)
                }
            ],
        )

        print("==================================================================================================")
        print(response.choices[0].message.content)

if __name__ == "__main__":
    query_assistant()

