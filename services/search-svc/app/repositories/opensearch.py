"""OpenSearch repository for search service."""

from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from opensearchpy import OpenSearch, exceptions
from opensearchpy.helpers import bulk

from ...shared.logging import LoggerMixin
from ..models import SearchResult, SearchResponse, IndexDocument


class SearchRepository(LoggerMixin):
    """Repository for search operations using OpenSearch."""
    
    def __init__(self, opensearch_client: OpenSearch, index_prefix: str = "ins"):
        self.client = opensearch_client
        self.index_prefix = index_prefix
        self.claims_index = f"{index_prefix}-claims"
        self.policies_index = f"{index_prefix}-policies"
    
    def create_indices(self) -> None:
        """Create OpenSearch indices with proper mappings."""
        # Claims index mapping
        claims_mapping = {
            "mappings": {
                "properties": {
                    "claimId": {"type": "keyword"},
                    "policyId": {"type": "keyword"},
                    "customerId": {"type": "keyword"},
                    "customerName": {
                        "type": "text",
                        "fields": {
                            "keyword": {"type": "keyword"}
                        }
                    },
                    "status": {"type": "keyword"},
                    "amount": {"type": "double"},
                    "occurredAt": {"type": "date"},
                    "description": {"type": "text"},
                    "category": {"type": "keyword"},
                    "createdAt": {"type": "date"},
                    "updatedAt": {"type": "date"},
                    "type": {"type": "keyword"}
                }
            },
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "index.lifecycle.name": "claims-policy",
                "index.lifecycle.rollover_alias": "claims"
            }
        }
        
        # Policies index mapping
        policies_mapping = {
            "mappings": {
                "properties": {
                    "policyId": {"type": "keyword"},
                    "customerId": {"type": "keyword"},
                    "customerName": {
                        "type": "text",
                        "fields": {
                            "keyword": {"type": "keyword"}
                        }
                    },
                    "status": {"type": "keyword"},
                    "premium": {"type": "double"},
                    "effectiveDate": {"type": "date"},
                    "expirationDate": {"type": "date"},
                    "coverageType": {"type": "keyword"},
                    "deductible": {"type": "double"},
                    "coverageLimit": {"type": "double"},
                    "createdAt": {"type": "date"},
                    "updatedAt": {"type": "date"},
                    "type": {"type": "keyword"}
                }
            },
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "index.lifecycle.name": "policies-policy",
                "index.lifecycle.rollover_alias": "policies"
            }
        }
        
        # Create indices if they don't exist
        for index_name, mapping in [
            (self.claims_index, claims_mapping),
            (self.policies_index, policies_mapping)
        ]:
            if not self.client.indices.exists(index=index_name):
                self.client.indices.create(index=index_name, body=mapping)
                self.logger.info(f"Created index: {index_name}")
    
    def search(
        self, 
        query: str, 
        page: int = 1, 
        size: int = 20,
        filters: Optional[Dict[str, Any]] = None,
        sort: Optional[str] = None
    ) -> SearchResponse:
        """Search across policies and claims."""
        try:
            # Build search query
            search_body = {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "multi_match": {
                                    "query": query,
                                    "fields": [
                                        "customerName^2",
                                        "description^1.5",
                                        "claimId",
                                        "policyId",
                                        "status",
                                        "category",
                                        "coverageType"
                                    ],
                                    "type": "best_fields",
                                    "fuzziness": "AUTO"
                                }
                            }
                        ]
                    }
                },
                "from": (page - 1) * size,
                "size": size,
                "_source": True
            }
            
            # Add filters
            if filters:
                filter_conditions = []
                for field, value in filters.items():
                    if isinstance(value, list):
                        filter_conditions.append({"terms": {field: value}})
                    else:
                        filter_conditions.append({"term": {field: value}})
                
                search_body["query"]["bool"]["filter"] = filter_conditions
            
            # Add sorting
            if sort:
                if sort.startswith("-"):
                    search_body["sort"] = [{sort[1:]: {"order": "desc"}}]
                else:
                    search_body["sort"] = [{sort: {"order": "asc"}}]
            
            # Search across both indices
            response = self.client.search(
                index=f"{self.claims_index},{self.policies_index}",
                body=search_body
            )
            
            # Process results
            results = []
            for hit in response["hits"]["hits"]:
                result = SearchResult(
                    id=hit["_source"].get("claimId") or hit["_source"].get("policyId"),
                    type="claim" if "claimId" in hit["_source"] else "policy",
                    score=hit["_score"],
                    source=hit["_source"]
                )
                results.append(result)
            
            # Calculate pagination
            total = response["hits"]["total"]["value"]
            total_pages = (total + size - 1) // size
            next_page = page + 1 if page < total_pages else None
            
            return SearchResponse(
                query=query,
                results=results,
                total=total,
                took=response["took"],
                page=page,
                size=size,
                next_page=next_page
            )
            
        except exceptions.OpenSearchException as e:
            self.logger.error("OpenSearch search failed", error=str(e), query=query)
            raise RuntimeError(f"Search failed: {str(e)}") from e
    
    def index_document(self, document: IndexDocument) -> bool:
        """Index a single document."""
        try:
            index_name = (
                self.claims_index if document.type == "claim" 
                else self.policies_index
            )
            
            # Prepare document for indexing
            doc_body = document.data.copy()
            doc_body["type"] = document.type
            doc_body["indexedAt"] = document.indexed_at.isoformat()
            
            response = self.client.index(
                index=index_name,
                id=document.id,
                body=doc_body
            )
            
            self.logger.info("Document indexed", id=document.id, type=document.type)
            return response["result"] in ["created", "updated"]
            
        except exceptions.OpenSearchException as e:
            self.logger.error("Failed to index document", error=str(e), id=document.id)
            return False
    
    def bulk_index(self, documents: List[IndexDocument]) -> Tuple[int, int]:
        """Bulk index multiple documents."""
        try:
            actions = []
            for doc in documents:
                index_name = (
                    self.claims_index if doc.type == "claim" 
                    else self.policies_index
                )
                
                doc_body = doc.data.copy()
                doc_body["type"] = doc.type
                doc_body["indexedAt"] = doc.indexed_at.isoformat()
                
                action = {
                    "_index": index_name,
                    "_id": doc.id,
                    "_source": doc_body
                }
                actions.append(action)
            
            # Perform bulk indexing
            success_count, failed_items = bulk(
                self.client,
                actions,
                stats_only=True,
                raise_on_error=False
            )
            
            failed_count = len(failed_items) if failed_items else 0
            self.logger.info(
                "Bulk indexing completed",
                success_count=success_count,
                failed_count=failed_count
            )
            
            return success_count, failed_count
            
        except exceptions.OpenSearchException as e:
            self.logger.error("Bulk indexing failed", error=str(e))
            return 0, len(documents)
    
    def delete_document(self, doc_id: str, doc_type: str) -> bool:
        """Delete a document from the index."""
        try:
            index_name = (
                self.claims_index if doc_type == "claim" 
                else self.policies_index
            )
            
            response = self.client.delete(index=index_name, id=doc_id)
            self.logger.info("Document deleted", id=doc_id, type=doc_type)
            return response["result"] == "deleted"
            
        except exceptions.NotFoundError:
            self.logger.warning("Document not found for deletion", id=doc_id)
            return False
        except exceptions.OpenSearchException as e:
            self.logger.error("Failed to delete document", error=str(e), id=doc_id)
            return False
    
    def get_document(self, doc_id: str, doc_type: str) -> Optional[Dict[str, Any]]:
        """Get a document by ID."""
        try:
            index_name = (
                self.claims_index if doc_type == "claim" 
                else self.policies_index
            )
            
            response = self.client.get(index=index_name, id=doc_id)
            return response["_source"]
            
        except exceptions.NotFoundError:
            return None
        except exceptions.OpenSearchException as e:
            self.logger.error("Failed to get document", error=str(e), id=doc_id)
            return None
