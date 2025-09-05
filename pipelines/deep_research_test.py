"""
title: Deep Research Pipeline
author: AI Assistant
author_url: Unknown
git_url: https://github.com/open-webui/pipelines
description: A pipeline that enables deep research functionality by iteratively searching the web, analyzing results, and determining when sufficient information has been gathered.
required_open_webui_version: 0.4.3
requirements: requests, asyncio, duckduckgo-search
version: 1.0.0
licence: MIT
"""

from typing import List, Union, Generator, Iterator, Optional, Dict, Any
from pydantic import BaseModel, Field
import requests
import json
import time
import asyncio
from datetime import datetime
import os
from logging import getLogger

logger = getLogger(__name__)
logger.setLevel("INFO")

class Pipeline:
    class Valves(BaseModel):
        # LLM Configuration
        OPENAI_API_BASE_URL: str = Field(
            default="https://api.openai.com/v1",
            description="Base URL for the LLM API (OpenAI compatible)"
        )
        OPENAI_API_KEY: str = Field(
            default="",
            description="API key for the LLM service"
        )
        LLM_MODEL: str = Field(
            default="gpt-4o-mini",
            description="Model to use for research coordination and analysis"
        )
        
        # Web Search Configuration
        SEARCH_ENGINE: str = Field(
            default="duckduckgo",
            description="Search engine to use (duckduckgo, brave, serper, etc.)"
        )
        BRAVE_API_KEY: str = Field(
            default="",
            description="Brave Search API key (if using Brave)"
        )
        SERPER_API_KEY: str = Field(
            default="",
            description="Serper API key (if using Serper)"
        )
        TAVILY_API_KEY: str = Field(
            default="",
            description="Tavily API key (if using Tavily)"
        )
        
        # Research Parameters
        MAX_SEARCH_ITERATIONS: int = Field(
            default=3,
            description="Maximum number of search iterations before stopping"
        )
        RESULTS_PER_SEARCH: int = Field(
            default=5,
            description="Number of search results to retrieve per search"
        )
        MAX_CONTENT_LENGTH: int = Field(
            default=2000,
            description="Maximum characters to extract from each web page"
        )
        SEARCH_TIMEOUT: int = Field(
            default=10,
            description="Timeout in seconds for web requests"
        )
        
        # Research Behavior
        ENABLE_CONTENT_EXTRACTION: bool = Field(
            default=True,
            description="Whether to extract content from search result URLs"
        )
        ENABLE_ITERATIVE_REFINEMENT: bool = Field(
            default=True,
            description="Whether to refine search terms based on previous results"
        )
        RESEARCH_THOROUGHNESS: str = Field(
            default="balanced",
            description="Research thoroughness level: quick, balanced, or comprehensive"
        )

    def __init__(self):
        logger.debug("Initializing Deep Research Pipeline")
        self.name = "Deep Research Pipeline"
        
        # Initialize valve parameters
        self.valves = self.Valves(
            **{k: os.getenv(k, v.default) for k, v in self.Valves.model_fields.items()}
        )
        
        self.search_history = []
        self.accumulated_context = ""

    async def on_startup(self):
        logger.debug("Starting up Deep Research Pipeline")
        logger.debug(f"on_startup: {self.name}")

    async def on_shutdown(self):
        logger.debug("Shutting down Deep Research Pipeline")
        logger.debug(f"on_shutdown: {self.name}")

    def pipe(
        self, 
        user_message: str, 
        model_id: str, 
        messages: List[dict], 
        body: dict
    ) -> Union[str, Generator, Iterator]:
        """
        Main pipeline function that orchestrates the deep research process
        """
        logger.debug(f"Processing message: {user_message[:50]}...")
        logger.debug(f"Pipeline Model ID: {model_id}, Stream: {body.get('stream', False)}")
        logger.debug(f"LLM Model for API calls: {self.valves.LLM_MODEL}")
        
        try:
            # Check if API key is configured
            if not self.valves.OPENAI_API_KEY or self.valves.OPENAI_API_KEY.strip() == "":
                yield "❌ **Configuration Error**: OpenAI API key is not configured. Please set your API key in the pipeline valves to use the deep research functionality."
                return
            
            # Handle simple greetings and basic questions without deep research
            simple_responses = {
                "hi": "Hello! I'm the Deep Research Pipeline. I can help you conduct comprehensive research on complex topics. Try asking me a research question that requires gathering information from multiple sources!",
                "hello": "Hello! I'm the Deep Research Pipeline. I can help you conduct comprehensive research on complex topics. Try asking me a research question that requires gathering information from multiple sources!",
                "how are you": "I'm functioning well and ready to help with deep research! I can search the web, analyze information from multiple sources, and provide comprehensive answers to complex questions. What would you like to research?",
                "what can you do": "I'm a deep research pipeline that can:\n\n🔍 **Search multiple sources** (DuckDuckGo, Brave, Serper, Tavily)\n🧠 **Analyze and synthesize** information from multiple searches\n📊 **Iterate and refine** searches based on findings\n💡 **Generate comprehensive** research summaries\n\nTry asking me a research question like 'What is artificial intelligence?' or 'How does climate change affect agriculture?'"
            }
            
            question_lower = user_message.lower().strip()
            if question_lower in simple_responses:
                yield simple_responses[question_lower]
                return

            # Initialize research session
            self.search_history = []
            self.accumulated_context = ""
            
            # Use the configured LLM model for API calls (model_id is the pipeline name)
            current_model = self.valves.LLM_MODEL
            
            streaming = body.get("stream", True)
            
            if streaming:
                yield from self._conduct_research_streaming(user_message, current_model)
            else:
                result = ""
                for chunk in self._conduct_research_streaming(user_message, current_model):
                    result += chunk
                return result
                
        except Exception as e:
            logger.error(f"Error in deep research pipeline: {str(e)}")
            error_msg = f"I encountered an error while conducting research: {str(e)}"
            if body.get("stream", True):
                yield error_msg
            else:
                return error_msg

    def _conduct_research_streaming(self, question: str, model: str) -> Generator[str, None, None]:
        """
        Conducts iterative research on the given question with streaming output
        """
        yield "🔍 **Starting deep research...**\n\n"
        
        iteration = 0
        max_iterations = self.valves.MAX_SEARCH_ITERATIONS
        
        # Initial analysis of the question
        yield "🧠 **Analyzing question and planning research strategy...**\n\n"
        
        try:
            search_strategy = self._analyze_question(question, model)
            yield f"📋 **Research Strategy**: {search_strategy}\n\n"
        except Exception as e:
            logger.error(f"Error analyzing question: {e}")
            search_strategy = f"Research strategy for: {question}"
        
        while iteration < max_iterations:
            iteration += 1
            
            yield f"🔍 **Research iteration {iteration}/{max_iterations}...**\n\n"
            
            # Generate search queries based on current knowledge
            try:
                search_queries = self._generate_search_queries(
                    question, search_strategy, iteration, model
                )
                
                if not search_queries:
                    yield "No more search queries needed.\n\n"
                    break
                    
                yield f"🔎 **Search queries**: {', '.join(search_queries)}\n\n"
                
            except Exception as e:
                logger.error(f"Error generating search queries: {e}")
                search_queries = [question]  # Fallback
            
            # Perform web searches
            yield "🌐 **Searching the web...**\n\n"
            search_results = self._perform_searches(search_queries)
            
            if not search_results:
                yield "No search results found.\n\n"
                break
            
            # Extract and analyze content
            yield "📖 **Extracting and analyzing content...**\n\n"
            extracted_content = self._extract_content(search_results)
            
            # Update accumulated context
            self.accumulated_context += f"\n\n--- Research Iteration {iteration} ---\n"
            self.accumulated_context += extracted_content
            
            # Show some results to user
            yield f"📊 **Found {len(search_results)} relevant sources:**\n\n"
            
            # Display the search results with titles and links
            for i, result in enumerate(search_results[:5], 1):  # Show first 5 results
                title = result.get('title', 'No title')
                link = result.get('link', 'No link')
                snippet = result.get('snippet', 'No snippet')
                
                yield f"**{i}. {title}**\n"
                yield f"🔗 {link}\n"
                yield f"📝 {snippet[:150]}{'...' if len(snippet) > 150 else ''}\n\n"
            
            yield "---\n\n"
            
            # Determine if more research is needed
            yield "🤔 **Analyzing gathered information...**\n\n"
            
            try:
                continuation_decision = self._should_continue_research(
                    question, self.accumulated_context, iteration, max_iterations, model
                )
                
                if not continuation_decision.get("continue", False):
                    yield "✅ **Research complete. Generating final answer...**\n\n"
                    break
                else:
                    # Update search strategy for next iteration
                    search_strategy = continuation_decision.get("refined_strategy", search_strategy)
                    yield f"🔄 **Continuing research**: {continuation_decision.get('reason', 'Need more information')}\n\n"
                    
            except Exception as e:
                logger.error(f"Error in continuation decision: {e}")
                # Conservative fallback - continue if we have iterations left
                if iteration < max_iterations - 1:
                    yield "🔄 **Continuing research** (fallback decision)\n\n"
                else:
                    yield "✅ **Research complete. Generating final answer...**\n\n"
                    break
        
        # Generate final comprehensive response
        yield "🎯 **Generating comprehensive research summary...**\n\n"
        
        try:
            final_response = self._generate_final_response(question, self.accumulated_context, model)
            yield final_response
        except Exception as e:
            logger.error(f"Error generating final response: {e}")
            yield f"I gathered extensive research on '{question}' but encountered an error generating the final response. Here's what I found:\n\n{self.accumulated_context[:1000]}..."
        
        # Add research metadata
        yield f"\n\n---\n**🔍 Research Summary:**\n"
        yield f"- **Searches performed**: {len(self.search_history)}\n"
        yield f"- **Search queries used**: {', '.join([h['query'] for h in self.search_history])}\n"
        yield f"- **Research completed at**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"

    def _analyze_question(self, question: str, model: str) -> str:
        """
        Analyzes the user's question to develop a research strategy
        """
        prompt = f"""
        Analyze this research question and develop a comprehensive research strategy:
        
        Question: {question}
        
        Please provide:
        1. Key topics and concepts to research
        2. Potential subtopics and related areas
        3. Types of sources that would be most valuable
        4. Research approach (broad vs. specific, recent vs. historical, etc.)
        
        Format your response as a concise research strategy outline.
        """
        
        try:
            response = self._call_llm(prompt, model, max_tokens=500)
            return response
        except Exception as e:
            logger.error(f"Error analyzing question: {e}")
            return f"Research strategy for: {question}"

    def _generate_search_queries(
        self, 
        question: str, 
        strategy: str, 
        iteration: int,
        model: str
    ) -> List[str]:
        """
        Generates targeted search queries based on the question, strategy, and current iteration
        """
        context_info = ""
        if self.accumulated_context and iteration > 1:
            context_info = f"\n\nPrevious research findings:\n{self.accumulated_context[-1000:]}"
        
        prompt = f"""
        Generate targeted web search queries for this research question:
        
        Question: {question}
        Research Strategy: {strategy}
        Iteration: {iteration}
        {context_info}
        
        Based on the above, generate 2-3 specific search queries that will help gather comprehensive information.
        
        Guidelines:
        - Make queries specific and targeted
        - Avoid overly broad terms
        - Include relevant keywords and phrases
        - Consider different angles and perspectives
        {f"- Build on previous findings to fill knowledge gaps" if iteration > 1 else ""}
        
        Return only the search queries, one per line, without numbering or extra text.
        """
        
        try:
            response = self._call_llm(prompt, model, max_tokens=200)
            queries = [q.strip() for q in response.split('\n') if q.strip()]
            return queries[:3]  # Limit to 3 queries
        except Exception as e:
            logger.error(f"Error generating search queries: {e}")
            return [question]  # Fallback to original question

    def _perform_searches(self, queries: List[str]) -> List[Dict[str, Any]]:
        """
        Performs web searches for the given queries
        """
        all_results = []
        
        for query in queries:
            try:
                results = self._search_web(query)
                all_results.extend(results)
                
                # Record search in history
                self.search_history.append({
                    "query": query,
                    "timestamp": datetime.now().isoformat(),
                    "results_count": len(results)
                })
                
                # Small delay between searches
                time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Error searching for '{query}': {e}")
                continue
        
        return all_results

    def _search_web(self, query: str) -> List[Dict[str, Any]]:
        """
        Performs a web search using the configured search engine
        """
        engine = self.valves.SEARCH_ENGINE.lower()
        
        if engine == "brave" and self.valves.BRAVE_API_KEY:
            return self._search_brave(query)
        elif engine == "serper" and self.valves.SERPER_API_KEY:
            return self._search_serper(query)
        elif engine == "tavily" and self.valves.TAVILY_API_KEY:
            return self._search_tavily(query)
        else:
            # Fallback to DuckDuckGo (simplified)
            return self._search_duckduckgo(query)

    def _search_duckduckgo(self, query: str) -> List[Dict[str, Any]]:
        """
        Search using DuckDuckGo
        """
        try:
            from duckduckgo_search import DDGS
            
            results = []
            with DDGS() as ddgs:
                search_results = ddgs.text(
                    query, 
                    max_results=self.valves.RESULTS_PER_SEARCH,
                    region="wt-wt",  # Worldwide
                    safesearch="moderate"
                )
                
                for result in search_results:
                    results.append({
                        "title": result.get("title", ""),
                        "link": result.get("href", ""),
                        "snippet": result.get("body", "")
                    })
            
            return results
        except ImportError:
            logger.error("duckduckgo-search library not installed. Install with: pip install duckduckgo-search")
            # Fallback to mock data if library not available
            return [{
                "title": f"Search result for: {query}",
                "link": "https://example.com",
                "snippet": f"This would be content related to {query} (mock result - install duckduckgo-search for real results)"
            }]
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
            return []

    def _search_brave(self, query: str) -> List[Dict[str, Any]]:
        """
        Search using Brave Search API
        """
        try:
            url = "https://api.search.brave.com/res/v1/web/search"
            headers = {
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
                "X-Subscription-Token": self.valves.BRAVE_API_KEY
            }
            params = {
                "q": query,
                "count": self.valves.RESULTS_PER_SEARCH
            }
            
            response = requests.get(
                url, headers=headers, params=params, 
                timeout=self.valves.SEARCH_TIMEOUT
            )
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            for item in data.get("web", {}).get("results", []):
                results.append({
                    "title": item.get("title", ""),
                    "link": item.get("url", ""),
                    "snippet": item.get("description", "")
                })
            
            return results
        except Exception as e:
            logger.error(f"Brave search error: {e}")
            return []

    def _search_serper(self, query: str) -> List[Dict[str, Any]]:
        """
        Search using Serper API
        """
        try:
            url = "https://google.serper.dev/search"
            headers = {
                "X-API-KEY": self.valves.SERPER_API_KEY,
                "Content-Type": "application/json"
            }
            data = {"q": query, "num": self.valves.RESULTS_PER_SEARCH}
            
            response = requests.post(
                url, headers=headers, json=data,
                timeout=self.valves.SEARCH_TIMEOUT
            )
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            for item in data.get("organic", []):
                results.append({
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", "")
                })
            
            return results
        except Exception as e:
            logger.error(f"Serper search error: {e}")
            return []

    def _search_tavily(self, query: str) -> List[Dict[str, Any]]:
        """
        Search using Tavily API
        """
        try:
            url = "https://api.tavily.com/search"
            headers = {
                "Content-Type": "application/json"
            }
            data = {
                "api_key": self.valves.TAVILY_API_KEY,
                "query": query,
                "search_depth": "basic",
                "include_answer": False,
                "include_images": False,
                "include_raw_content": False,
                "max_results": self.valves.RESULTS_PER_SEARCH
            }
            
            response = requests.post(
                url, headers=headers, json=data,
                timeout=self.valves.SEARCH_TIMEOUT
            )
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            for item in data.get("results", []):
                results.append({
                    "title": item.get("title", ""),
                    "link": item.get("url", ""),
                    "snippet": item.get("content", "")
                })
            
            return results
        except Exception as e:
            logger.error(f"Tavily search error: {e}")
            return []

    def _extract_content(self, search_results: List[Dict[str, Any]]) -> str:
        """
        Extracts and processes content from search results
        """
        if not self.valves.ENABLE_CONTENT_EXTRACTION:
            # Return just the snippets if content extraction is disabled
            content_parts = []
            for result in search_results:
                content_parts.append(f"Title: {result.get('title', '')}")
                content_parts.append(f"URL: {result.get('link', '')}")
                content_parts.append(f"Snippet: {result.get('snippet', '')}")
                content_parts.append("---")
            return "\n".join(content_parts)
        
        content_parts = []
        
        for i, result in enumerate(search_results[:self.valves.RESULTS_PER_SEARCH]):
            try:
                # Extract content from URL (simplified - in production use proper scraping)
                title = result.get("title", "")
                url = result.get("link", "")
                snippet = result.get("snippet", "")
                
                content_parts.append(f"Source {i+1}: {title}")
                content_parts.append(f"URL: {url}")
                content_parts.append(f"Content: {snippet}")
                content_parts.append("---")
                
            except Exception as e:
                logger.error(f"Error extracting content from {result.get('link', '')}: {e}")
                continue
        
        return "\n".join(content_parts)

    def _should_continue_research(
        self, 
        question: str, 
        accumulated_context: str, 
        current_iteration: int, 
        max_iterations: int,
        model: str
    ) -> Dict[str, Any]:
        """
        Determines whether to continue research based on gathered information
        """
        if not self.valves.ENABLE_ITERATIVE_REFINEMENT:
            return {"continue": False, "reason": "Iterative refinement disabled"}
        
        if current_iteration >= max_iterations:
            return {"continue": False, "reason": "Maximum iterations reached"}
        
        prompt = f"""
        Analyze the research progress and determine if more information is needed:
        
        Original Question: {question}
        Current Iteration: {current_iteration}/{max_iterations}
        
        Information Gathered So Far:
        {accumulated_context[-2000:]}  # Last 2000 chars to avoid token limits
        
        Based on the original question and the information gathered, determine:
        1. Is the current information sufficient to provide a comprehensive answer?
        2. Are there important knowledge gaps that need to be filled?
        3. What specific aspects need more research (if any)?
        
        Respond with a JSON object containing:
        - "continue": boolean (true if more research is needed)
        - "reason": string (explanation for the decision)
        - "refined_strategy": string (updated research strategy if continuing)
        - "confidence": number (0-1, confidence that current info is sufficient)
        
        Example response:
        {{"continue": true, "reason": "Need more recent data on market trends", "refined_strategy": "Focus on 2024 market data and regulatory changes", "confidence": 0.3}}
        """
        
        try:
            response = self._call_llm(prompt, model, max_tokens=300)
            
            # Try to parse JSON response
            try:
                decision = json.loads(response)
                return decision
            except json.JSONDecodeError:
                # Fallback if LLM doesn't return valid JSON
                continue_research = "continue" in response.lower() and "true" in response.lower()
                return {
                    "continue": continue_research,
                    "reason": "Parsed from LLM response",
                    "confidence": 0.5
                }
                
        except Exception as e:
            logger.error(f"Error in continuation decision: {e}")
            # Conservative fallback - continue if we have iterations left
            return {
                "continue": current_iteration < max_iterations - 1,
                "reason": "Error in decision making, defaulting to continue",
                "confidence": 0.2
            }

    def _generate_final_response(
        self, 
        question: str, 
        accumulated_context: str,
        model: str
    ) -> str:
        """
        Generates the final comprehensive response based on all gathered information
        """
        prompt = f"""
        You are a research assistant providing a comprehensive answer based on extensive web research.
        
        Original Question: {question}
        
        Research Findings:
        {accumulated_context}
        
        Please provide a comprehensive, well-structured answer that:
        1. Directly addresses the original question
        2. Synthesizes information from multiple sources
        3. Presents key findings and insights
        4. Acknowledges any limitations or uncertainties
        5. Is well-organized with clear sections/points
        
        Make sure to:
        - Be factual and accurate
        - Cite information appropriately (e.g., "According to research findings...")
        - Provide a balanced perspective
        - Be thorough but concise
        - Use clear, accessible language
        
        Format your response as a comprehensive research summary.
        """
        
        try:
            response = self._call_llm(prompt, model, max_tokens=2000)
            return response
            
        except Exception as e:
            logger.error(f"Error generating final response: {e}")
            return f"I gathered extensive research on '{question}' but encountered an error generating the final response. Here's what I found:\n\n{accumulated_context[:1000]}..."

    def _call_llm(self, prompt: str, model: str, max_tokens: int = 1000) -> str:
        """
        Makes a call to the configured LLM
        """
        logger.debug(f"Making LLM API call with model: {model}")
        
        headers = {
            "Authorization": f"Bearer {self.valves.OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.6
        }
        
        url = f"{self.valves.OPENAI_API_BASE_URL}/chat/completions"
        
        try:
            response = requests.post(
                url,
                headers=headers,
                json=data,
                timeout=300
            )
            response.raise_for_status()
            
            result = response.json()
            return result["choices"][0]["message"]["content"]
            
        except Exception as e:
            # Debug logging for LLM request errors
            logger.error(f"LLM Request Error: {str(e)}")
            logger.error(f"Request URL: {url}")
            logger.error(f"Request Headers: {headers}")
            logger.error(f"Request Body: {json.dumps(data, indent=2)}")
            
            # Also print to console for immediate debugging
            print(f"❌ LLM Request Error: {str(e)}")
            print(f"🔗 Request URL: {url}")
            print(f"📋 Request Headers: {headers}")
            print(f"📄 Request Body: {json.dumps(data, indent=2)}")
            
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response Status Code: {e.response.status_code}")
                logger.error(f"Response Text: {e.response.text}")
                print(f"📊 Response Status Code: {e.response.status_code}")
                print(f"📝 Response Text: {e.response.text}")
            
            raise e 