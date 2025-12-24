"""Value objects for session-related types."""
from typing import Any


class SessionTopic:
    """Value object for session topic with validation."""
    
    def __init__(self, topic: str) -> None:
        """Initialize session topic.
        
        Args:
            topic: Session topic string
            
        Raises:
            ValueError: If topic is empty or invalid
        """
        if not topic or not isinstance(topic, str):
            raise ValueError("Session topic must be a non-empty string")
        self._topic = topic
    
    def __str__(self) -> str:
        """Return topic as string."""
        return self._topic
    
    def __repr__(self) -> str:
        """Return representation."""
        return f"SessionTopic('{self._topic}')"
    
    def __eq__(self, other: Any) -> bool:
        """Check equality."""
        if isinstance(other, SessionTopic):
            return self._topic == other._topic
        if isinstance(other, str):
            return self._topic == other
        return False
    
    def __hash__(self) -> int:
        """Return hash."""
        return hash(self._topic)


class ProposalId:
    """Value object for proposal ID with validation."""
    
    def __init__(self, proposal_id: int) -> None:
        """Initialize proposal ID.
        
        Args:
            proposal_id: Proposal ID integer
            
        Raises:
            ValueError: If proposal_id is not a positive integer
        """
        if not isinstance(proposal_id, int) or proposal_id <= 0:
            raise ValueError("Proposal ID must be a positive integer")
        self._id = proposal_id
    
    def __int__(self) -> int:
        """Return ID as integer."""
        return self._id
    
    def __repr__(self) -> str:
        """Return representation."""
        return f"ProposalId({self._id})"
    
    def __eq__(self, other: Any) -> bool:
        """Check equality."""
        if isinstance(other, ProposalId):
            return self._id == other._id
        if isinstance(other, int):
            return self._id == other
        return False
    
    def __hash__(self) -> int:
        """Return hash."""
        return hash(self._id)
