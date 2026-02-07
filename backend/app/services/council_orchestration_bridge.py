"""
AI Council Orchestration Bridge for WebSocket integration.

This module bridges the AI Council Core with the FastAPI backend,
hooking into orchestration events to send real-time WebSocket updates.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from ai_council.factory import AICouncilFactory
from ai_council.core.models import ExecutionMode, FinalResponse, Task
from ai_council.core.interfaces import OrchestrationLayer
from ai_council.utils.config import AICouncilConfig

from app.services.websocket_manager import WebSocketManager
from app.services.cloud_ai.model_registry import MODEL_REGISTRY
from app.services.cloud_ai.adapter import CloudAIAdapter
from app.services.execution_mode_config import get_execution_mode_config
from app.core.config import settings

logger = logging.getLogger(__name__)


class CouncilOrchestrationBridge:
    """
    Bridges AI Council Core with WebSocket updates for real-time orchestration tracking.
    
    This class:
    - Initializes AI Council with cloud AI adapters
    - Hooks into orchestration events at each layer
    - Sends WebSocket messages for real-time progress updates
    - Manages the complete request processing lifecycle
    """
    
    def __init__(self, websocket_manager: WebSocketManager):
        """
        Initialize the orchestration bridge.
        
        Args:
            websocket_manager: WebSocket manager for sending real-time updates
        """
        self.ws_manager = websocket_manager
        self.ai_council: Optional[OrchestrationLayer] = None
        self.current_request_id: Optional[str] = None
        self._pending_routing_assignments: List[Dict[str, Any]] = []
        
        logger.info("CouncilOrchestrationBridge initialized")
    
    async def process_request(
        self,
        request_id: str,
        user_input: str,
        execution_mode: ExecutionMode
    ) -> FinalResponse:
        """
        Process a request through AI Council with real-time WebSocket updates.
        
        This method:
        1. Initializes AI Council with cloud adapters
        2. Sets up event hooks for WebSocket updates
        3. Processes the request through AI Council
        4. Returns the final response
        
        Args:
            request_id: Unique identifier for the request
            user_input: User's input text to process
            execution_mode: Execution mode (FAST, BALANCED, BEST_QUALITY)
            
        Returns:
            FinalResponse: The final synthesized response from AI Council
        """
        self.current_request_id = request_id
        self._pending_routing_assignments = []
        
        try:
            logger.info(f"Processing request {request_id} in {execution_mode.value} mode")
            
            # Initialize AI Council with cloud AI adapters and execution mode config
            self.ai_council = self._create_ai_council(execution_mode)
            
            # Set up event hooks for WebSocket updates
            self._setup_event_hooks(request_id)
            
            # Send initial processing started message
            await self.ws_manager.broadcast_progress(
                request_id,
                "processing_started",
                {
                    "execution_mode": execution_mode.value,
                    "message": "Request processing started"
                }
            )
            
            # Process request through AI Council in a thread pool
            # (AI Council is synchronous, so we run it in a thread)
            response = await asyncio.to_thread(
                self.ai_council.process_request,
                user_input,
                execution_mode
            )
            
            # Send any pending routing assignments that were captured during execution
            if self._pending_routing_assignments:
                await self.ws_manager.broadcast_progress(
                    request_id,
                    "routing_complete",
                    {
                        "assignments": self._pending_routing_assignments,
                        "totalSubtasks": len(self._pending_routing_assignments),
                        "message": f"Routed {len(self._pending_routing_assignments)} subtasks to appropriate models"
                    }
                )
                logger.info(f"Sent routing_complete message with {len(self._pending_routing_assignments)} assignments")
            
            logger.info(f"Request {request_id} processed successfully")
            return response
            
        except Exception as e:
            logger.error(f"Error processing request {request_id}: {e}", exc_info=True)
            
            # Send error message via WebSocket
            await self.ws_manager.broadcast_progress(
                request_id,
                "error",
                {
                    "message": "Request processing failed",
                    "error": str(e)
                }
            )
            
            # Return error response
            from ai_council.core.models import FinalResponse
            return FinalResponse(
                content="",
                overall_confidence=0.0,
                success=False,
                error_message=f"Processing failed: {str(e)}"
            )
        finally:
            self.current_request_id = None
            self._pending_routing_assignments = []
    
    def _create_ai_council(self, execution_mode: ExecutionMode) -> OrchestrationLayer:
        """
        Create AI Council instance with cloud AI adapters.
        
        This method:
        1. Creates AI Council configuration with execution mode settings
        2. Initializes the factory
        3. Registers cloud AI models from MODEL_REGISTRY
        4. Returns the orchestration layer
        
        Args:
            execution_mode: The execution mode to configure AI Council with
        
        Returns:
            OrchestrationLayer: Configured AI Council orchestration layer
        """
        logger.info(f"Creating AI Council with cloud AI adapters for {execution_mode.value} mode")
        
        # Get execution mode configuration
        mode_config = get_execution_mode_config(execution_mode)
        logger.info(
            f"Execution mode config: parallelism={mode_config.max_parallel_executions}, "
            f"arbitration={mode_config.enable_arbitration}, "
            f"accuracy={mode_config.accuracy_requirement}, "
            f"cost_limit={mode_config.cost_limit}"
        )
        
        # Create AI Council configuration with execution mode settings
        config = AICouncilConfig()
        
        # Apply execution mode configuration to AI Council config
        config.execution.default_mode = execution_mode
        config.execution.max_parallel_executions = mode_config.max_parallel_executions
        config.execution.default_timeout_seconds = mode_config.timeout_seconds
        config.execution.max_retries = mode_config.max_retries
        config.execution.enable_arbitration = mode_config.enable_arbitration
        config.execution.enable_synthesis = mode_config.enable_synthesis
        config.execution.default_accuracy_requirement = mode_config.accuracy_requirement
        
        # Set cost limit if specified
        if mode_config.cost_limit is not None:
            config.cost.max_cost_per_request = mode_config.cost_limit
        
        # Create factory with configured settings
        factory = AICouncilFactory(config)
        
        # Register cloud AI models from our MODEL_REGISTRY
        for model_id, model_config in MODEL_REGISTRY.items():
            try:
                # Create cloud AI adapter
                adapter = CloudAIAdapter(
                    provider=model_config["provider"],
                    model_name=model_config["model_name"],
                    api_key=self._get_api_key(model_config["provider"])
                )
                
                # Create capabilities for the model
                from ai_council.core.models import ModelCapabilities, TaskType
                
                # Map capability strings to TaskType enums
                task_types = []
                for cap in model_config["capabilities"]:
                    try:
                        task_types.append(TaskType(cap.lower()))
                    except ValueError:
                        logger.warning(f"Unknown capability: {cap}")
                
                capabilities = ModelCapabilities(
                    task_types=task_types,
                    cost_per_token=(
                        model_config["cost_per_input_token"] + 
                        model_config["cost_per_output_token"]
                    ) / 2,
                    average_latency=model_config.get("average_latency", 2.0),
                    max_context_length=model_config.get("max_context", 8192),
                    reliability_score=model_config.get("reliability_score", 0.9),
                    strengths=model_config["capabilities"][:2],
                    weaknesses=[]
                )
                
                # Register model with factory's registry
                factory.model_registry.register_model(adapter, capabilities)
                
                logger.info(f"Registered cloud AI model: {model_id}")
                
            except Exception as e:
                logger.error(f"Failed to register model {model_id}: {e}")
                continue
        
        # Create and return orchestration layer
        orchestration_layer = factory.create_orchestration_layer()
        logger.info("AI Council orchestration layer created successfully")
        
        return orchestration_layer
    
    def _get_api_key(self, provider: str) -> str:
        """
        Get API key for a cloud provider.
        
        Args:
            provider: Provider name (groq, together, openrouter, huggingface)
            
        Returns:
            API key string
        """
        provider_key_map = {
            "groq": settings.GROQ_API_KEY,
            "together": settings.TOGETHER_API_KEY,
            "openrouter": settings.OPENROUTER_API_KEY,
            "huggingface": settings.HUGGINGFACE_API_KEY
        }
        
        api_key = provider_key_map.get(provider, "")
        if not api_key:
            logger.warning(f"No API key configured for provider: {provider}")
        
        return api_key
    
    def _setup_event_hooks(self, request_id: str) -> None:
        """
        Set up hooks to capture orchestration events and send WebSocket updates.
        
        This method wraps AI Council layer methods to intercept events and
        send real-time updates via WebSocket.
        
        Args:
            request_id: Unique identifier for the request
        """
        logger.info(f"Settings up event hooks for request {request_id}")
        
        # Hook into analysis layer
        self._hook_analysis_layer(request_id)
        
        # Hook into routing layer
        self._hook_routing_layer(request_id)
        
        # Hook into execution layer
        self._hook_execution_layer(request_id)
        
        # Hook into arbitration layer
        self._hook_arbitration_layer(request_id)
        
        # Hook into synthesis layer
        self._hook_synthesis_layer(request_id)
    
    def _hook_analysis_layer(self, request_id: str) -> None:
        """
        Hook into the analysis layer to send WebSocket updates.
        
        Wraps the analysis engine's methods to intercept analysis completion
        and send real-time updates.
        
        Args:
            request_id: Unique identifier for the request
        """
        analysis_engine = self.ai_council.analysis_engine
        
        # Store original methods
        original_analyze_intent = analysis_engine.analyze_intent
        original_determine_complexity = analysis_engine.determine_complexity
        
        # Track if analysis complete message has been sent
        analysis_complete_sent = {"sent": False}
        
        def hooked_analyze_intent(input_text: str):
            """Wrapped analyze_intent method."""
            result = original_analyze_intent(input_text)
            logger.debug(f"Analysis intent determined: {result.value if result else None}")
            return result
        
        def hooked_determine_complexity(input_text: str):
            """Wrapped determine_complexity method."""
            result = original_determine_complexity(input_text)
            logger.debug(f"Complexity determined: {result.value if result else None}")
            
            # Send analysis complete message after complexity is determined
            # (this is the last step in analysis)
            if not analysis_complete_sent["sent"]:
                analysis_complete_sent["sent"] = True
                
                # Get intent (call original method to avoid recursion)
                intent = original_analyze_intent(input_text)
                
                # Send WebSocket message asynchronously
                asyncio.create_task(
                    self.ws_manager.broadcast_progress(
                        request_id,
                        "analysis_complete",
                        {
                            "intent": intent.value if intent else None,
                            "complexity": result.value if result else None,
                            "message": "Input analysis completed"
                        }
                    )
                )
                logger.info(f"Analysis complete: intent={intent.value if intent else None}, complexity={result.value if result else None}")
            
            return result
        
        # Replace methods with hooked versions
        analysis_engine.analyze_intent = hooked_analyze_intent
        analysis_engine.determine_complexity = hooked_determine_complexity
        
        logger.debug("Analysis layer hooks installed")
    
    def _hook_routing_layer(self, request_id: str) -> None:
        """
        Hook into the routing layer to send WebSocket updates.
        
        Wraps the orchestration layer's _execute_parallel_group method to intercept
        routing decisions and send real-time updates about model assignments.
        
        Args:
            request_id: Unique identifier for the request
        """
        # Store original method
        original_execute_parallel_group = self.ai_council._execute_parallel_group
        
        # Track if routing complete message has been sent
        routing_complete_sent = {"sent": False}
        
        # Store routing assignments to be sent after thread execution
        self._pending_routing_assignments = []
        
        def hooked_execute_parallel_group(subtasks: List, execution_mode):
            """Wrapped _execute_parallel_group method."""
            
            # Before executing, capture routing decisions
            if not routing_complete_sent["sent"]:
                routing_complete_sent["sent"] = True
                
                # Collect model assignments for each subtask
                assignments = []
                
                for subtask in subtasks:
                    try:
                        # Get available models for this task type
                        available_models = [
                            m.get_model_id() 
                            for m in self.ai_council.model_registry.get_models_for_task_type(subtask.task_type)
                        ]
                        
                        if available_models:
                            # Use cost optimizer to determine which model will be selected
                            optimization = self.ai_council.cost_optimizer.optimize_model_selection(
                                subtask, execution_mode, available_models
                            )
                            
                            assignments.append({
                                "subtaskId": subtask.id,
                                "subtaskContent": subtask.content[:100],  # First 100 chars
                                "taskType": subtask.task_type.value if subtask.task_type else "unknown",
                                "modelId": optimization.recommended_model,
                                "reason": optimization.reasoning,
                                "estimatedCost": optimization.estimated_cost,
                                "estimatedTime": optimization.estimated_time
                            })
                            
                            logger.debug(f"Routing subtask {subtask.id} to {optimization.recommended_model}")
                        else:
                            logger.warning(f"No models available for subtask {subtask.id} with task type {subtask.task_type}")
                            
                    except Exception as e:
                        logger.error(f"Error capturing routing decision for subtask {subtask.id}: {e}")
                        # Continue with other subtasks
                        continue
                
                # Store assignments to be sent after thread execution
                if assignments:
                    self._pending_routing_assignments = assignments
                    logger.info(f"Routing complete: {len(assignments)} subtasks routed")
            
            # Call original method
            return original_execute_parallel_group(subtasks, execution_mode)
        
        # Replace method with hooked version
        self.ai_council._execute_parallel_group = hooked_execute_parallel_group
        
        logger.debug("Routing layer hooks installed")
    
    def _hook_execution_layer(self, request_id: str) -> None:
        """
        Hook into the execution layer to send WebSocket updates for subtask completion.
        
        Wraps the execution agent's execute method to intercept subtask execution
        completion and send real-time progress updates including confidence, cost,
        and execution time.
        
        Args:
            request_id: Unique identifier for the request
        """
        # Get execution agent from AI Council orchestration layer
        if not hasattr(self.ai_council, 'execution_agent'):
            logger.warning("AI Council does not have execution_agent attribute")
            return
        
        execution_agent = self.ai_council.execution_agent
        
        # Store original execute method
        original_execute = execution_agent.execute
        
        def hooked_execute(subtask, model):
            """Wrapped execute method."""
            # Call original execute method
            response = original_execute(subtask, model)
            
            # Send WebSocket message with execution progress
            try:
                # Extract metrics from the response
                confidence = 0.0
                cost = 0.0
                execution_time = 0.0
                
                if response.self_assessment:
                    confidence = response.self_assessment.confidence_score
                    cost = response.self_assessment.estimated_cost or 0.0
                    execution_time = response.self_assessment.execution_time or 0.0
                
                # Prepare progress data
                progress_data = {
                    "subtaskId": subtask.id,
                    "subtaskContent": subtask.content[:100],  # First 100 chars
                    "modelId": response.model_used,
                    "status": "completed" if response.success else "failed",
                    "confidence": confidence,
                    "cost": cost,
                    "executionTime": execution_time,
                    "success": response.success
                }
                
                # Add error message if failed
                if not response.success and response.error_message:
                    progress_data["errorMessage"] = response.error_message
                
                # Send WebSocket message asynchronously
                asyncio.create_task(
                    self.ws_manager.broadcast_progress(
                        request_id,
                        "execution_progress",
                        progress_data
                    )
                )
                
                logger.info(
                    f"Execution progress: subtask={subtask.id}, "
                    f"model={response.model_used}, "
                    f"confidence={confidence:.2f}, "
                    f"cost=${cost:.4f}, "
                    f"time={execution_time:.2f}s"
                )
                
            except Exception as e:
                logger.error(f"Error sending execution progress update: {e}")
                # Don't fail the execution if WebSocket update fails
            
            return response
        
        # Replace method with hooked version
        execution_agent.execute = hooked_execute
        
        logger.debug("Execution layer hooks installed")
    
    def _hook_arbitration_layer(self, request_id: str) -> None:
        """
        Hook into the arbitration layer to send WebSocket updates for conflict resolution.
        
        Wraps the orchestration layer's _arbitrate_with_protection method to intercept
        arbitration decisions and send real-time updates including conflicting results
        and selected result with reasoning.
        
        Args:
            request_id: Unique identifier for the request
        """
        # Store original method
        original_arbitrate_with_protection = self.ai_council._arbitrate_with_protection
        
        def hooked_arbitrate_with_protection(responses):
            """Wrapped _arbitrate_with_protection method."""
            # Call original arbitration method
            arbitration_result = original_arbitrate_with_protection(responses)
            
            # Send WebSocket message with arbitration decisions
            try:
                # Check if there were any conflicts resolved
                if arbitration_result.conflicts_resolved:
                    # Prepare arbitration data
                    arbitration_data = {
                        "conflictsDetected": len(arbitration_result.conflicts_resolved),
                        "decisions": []
                    }
                    
                    # Add details for each conflict resolution
                    for resolution in arbitration_result.conflicts_resolved:
                        decision = {
                            "chosenResponseId": resolution.chosen_response_id,
                            "reasoning": resolution.reasoning,
                            "confidence": resolution.confidence
                        }
                        arbitration_data["decisions"].append(decision)
                    
                    # Add information about conflicting responses
                    # Group responses by subtask to show what was being arbitrated
                    conflicting_responses = []
                    for response in responses:
                        conflicting_responses.append({
                            "responseId": f"{response.subtask_id}_{response.model_used}",
                            "modelId": response.model_used,
                            "subtaskId": response.subtask_id,
                            "confidence": (
                                response.self_assessment.confidence_score 
                                if response.self_assessment else 0.0
                            ),
                            "success": response.success
                        })
                    
                    arbitration_data["conflictingResults"] = conflicting_responses
                    arbitration_data["message"] = (
                        f"Arbitration resolved {len(arbitration_result.conflicts_resolved)} "
                        f"conflicts between {len(responses)} responses"
                    )
                    
                    # Send WebSocket message asynchronously
                    asyncio.create_task(
                        self.ws_manager.broadcast_progress(
                            request_id,
                            "arbitration_decision",
                            arbitration_data
                        )
                    )
                    
                    logger.info(
                        f"Arbitration decision: resolved {len(arbitration_result.conflicts_resolved)} "
                        f"conflicts from {len(responses)} responses"
                    )
                else:
                    # No conflicts detected, but still send a message for transparency
                    arbitration_data = {
                        "conflictsDetected": 0,
                        "decisions": [],
                        "conflictingResults": [],
                        "message": f"No conflicts detected among {len(responses)} responses"
                    }
                    
                    asyncio.create_task(
                        self.ws_manager.broadcast_progress(
                            request_id,
                            "arbitration_decision",
                            arbitration_data
                        )
                    )
                    
                    logger.info(f"Arbitration: no conflicts detected among {len(responses)} responses")
                
            except Exception as e:
                logger.error(f"Error sending arbitration decision update: {e}")
                # Don't fail the arbitration if WebSocket update fails
            
            return arbitration_result
        
        # Replace method with hooked version
        self.ai_council._arbitrate_with_protection = hooked_arbitrate_with_protection
        
        logger.debug("Arbitration layer hooks installed")
    
    def _hook_synthesis_layer(self, request_id: str) -> None:
        """
        Hook into the synthesis layer to send WebSocket updates for synthesis progress.
        
        Wraps the orchestration layer's _synthesize_with_protection method to intercept
        synthesis progress and send real-time updates including synthesis progress and
        final response with all metadata.
        
        Args:
            request_id: Unique identifier for the request
        """
        # Store original method
        original_synthesize_with_protection = self.ai_council._synthesize_with_protection
        
        def hooked_synthesize_with_protection(validated_responses):
            """Wrapped _synthesize_with_protection method."""
            
            # Send synthesis started message
            try:
                asyncio.create_task(
                    self.ws_manager.broadcast_progress(
                        request_id,
                        "synthesis_progress",
                        {
                            "stage": "started",
                            "message": f"Beginning synthesis of {len(validated_responses)} validated responses",
                            "totalResponses": len(validated_responses)
                        }
                    )
                )
                logger.info(f"Synthesis started: processing {len(validated_responses)} validated responses")
            except Exception as e:
                logger.error(f"Error sending synthesis started update: {e}")
            
            # Call original synthesis method
            final_response = original_synthesize_with_protection(validated_responses)
            
            # Send synthesis complete message with final response and all metadata
            try:
                # Prepare comprehensive final response data
                final_response_data = {
                    "stage": "complete",
                    "content": final_response.content,
                    "overallConfidence": final_response.overall_confidence,
                    "success": final_response.success,
                    "modelsUsed": final_response.models_used if final_response.models_used else [],
                    "message": "Synthesis complete - final response generated"
                }
                
                # Add cost breakdown if available
                if final_response.cost_breakdown:
                    final_response_data["costBreakdown"] = {
                        "totalCost": final_response.cost_breakdown.total_cost,
                        "executionTime": final_response.cost_breakdown.execution_time,
                        "modelCosts": final_response.cost_breakdown.model_costs if hasattr(final_response.cost_breakdown, 'model_costs') else {},
                        "tokenUsage": final_response.cost_breakdown.token_usage if hasattr(final_response.cost_breakdown, 'token_usage') else {}
                    }
                
                # Add execution metadata if available
                if hasattr(final_response, 'execution_metadata') and final_response.execution_metadata:
                    metadata = final_response.execution_metadata
                    final_response_data["executionMetadata"] = {
                        "executionPath": metadata.execution_path if hasattr(metadata, 'execution_path') else [],
                        "totalExecutionTime": metadata.total_execution_time if hasattr(metadata, 'total_execution_time') else 0.0,
                        "parallelExecutions": metadata.parallel_executions if hasattr(metadata, 'parallel_executions') else 0
                    }
                
                # Add error message if synthesis failed
                if not final_response.success and final_response.error_message:
                    final_response_data["errorMessage"] = final_response.error_message
                
                # Send synthesis progress update
                asyncio.create_task(
                    self.ws_manager.broadcast_progress(
                        request_id,
                        "synthesis_progress",
                        final_response_data
                    )
                )
                
                # Also send final_response message for backwards compatibility
                asyncio.create_task(
                    self.ws_manager.broadcast_progress(
                        request_id,
                        "final_response",
                        final_response_data
                    )
                )
                
                logger.info(
                    f"Synthesis complete: confidence={final_response.overall_confidence:.2f}, "
                    f"success={final_response.success}, "
                    f"models={len(final_response.models_used) if final_response.models_used else 0}"
                )
                
            except Exception as e:
                logger.error(f"Error sending synthesis complete update: {e}")
                # Don't fail the synthesis if WebSocket update fails
            
            return final_response
        
        # Replace method with hooked version
        self.ai_council._synthesize_with_protection = hooked_synthesize_with_protection
        
        logger.debug("Synthesis layer hooks installed")


# Global instance (will be initialized in main.py)
council_bridge: Optional[CouncilOrchestrationBridge] = None


def get_council_bridge() -> CouncilOrchestrationBridge:
    """
    Get the global CouncilOrchestrationBridge instance.
    
    Returns:
        CouncilOrchestrationBridge: The global bridge instance
    """
    global council_bridge
    if council_bridge is None:
        from app.services.websocket_manager import websocket_manager
        council_bridge = CouncilOrchestrationBridge(websocket_manager)
    return council_bridge

