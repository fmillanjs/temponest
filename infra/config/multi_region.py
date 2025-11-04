"""
Multi-Region Support Configuration for Temponest

Handles region-aware routing, data residency, and failover
"""
from typing import Dict, List, Optional, Literal
from pydantic import BaseModel
import os


class RegionConfig(BaseModel):
    """Configuration for a single region"""
    name: str
    code: str  # e.g., "us-east-1", "eu-west-1"
    display_name: str
    agent_service_url: str
    scheduler_service_url: str
    database_url: str
    qdrant_url: str
    prometheus_url: str
    grafana_url: str
    is_active: bool = True
    priority: int = 0  # Higher priority regions are preferred
    data_residency: List[str] = []  # List of country codes for data residency


class MultiRegionConfig(BaseModel):
    """Multi-region configuration"""
    enabled: bool = False
    primary_region: str
    regions: Dict[str, RegionConfig]
    failover_enabled: bool = True
    health_check_interval: int = 30  # seconds
    routing_strategy: Literal["latency", "round_robin", "priority"] = "latency"


# Default multi-region configuration
DEFAULT_CONFIG = MultiRegionConfig(
    enabled=False,
    primary_region="us-east-1",
    regions={
        "us-east-1": RegionConfig(
            name="us-east-1",
            code="us-east-1",
            display_name="US East (N. Virginia)",
            agent_service_url="http://agents-us-east-1.temponest.com",
            scheduler_service_url="http://scheduler-us-east-1.temponest.com",
            database_url=os.getenv("DATABASE_URL_US_EAST_1", ""),
            qdrant_url=os.getenv("QDRANT_URL_US_EAST_1", ""),
            prometheus_url="http://prometheus-us-east-1.temponest.com",
            grafana_url="http://grafana-us-east-1.temponest.com",
            is_active=True,
            priority=1,
            data_residency=["US", "CA"],
        ),
        "eu-west-1": RegionConfig(
            name="eu-west-1",
            code="eu-west-1",
            display_name="EU West (Ireland)",
            agent_service_url="http://agents-eu-west-1.temponest.com",
            scheduler_service_url="http://scheduler-eu-west-1.temponest.com",
            database_url=os.getenv("DATABASE_URL_EU_WEST_1", ""),
            qdrant_url=os.getenv("QDRANT_URL_EU_WEST_1", ""),
            prometheus_url="http://prometheus-eu-west-1.temponest.com",
            grafana_url="http://grafana-eu-west-1.temponest.com",
            is_active=True,
            priority=1,
            data_residency=["GB", "IE", "FR", "DE", "IT", "ES"],
        ),
        "ap-south-1": RegionConfig(
            name="ap-south-1",
            code="ap-south-1",
            display_name="Asia Pacific (Mumbai)",
            agent_service_url="http://agents-ap-south-1.temponest.com",
            scheduler_service_url="http://scheduler-ap-south-1.temponest.com",
            database_url=os.getenv("DATABASE_URL_AP_SOUTH_1", ""),
            qdrant_url=os.getenv("QDRANT_URL_AP_SOUTH_1", ""),
            prometheus_url="http://prometheus-ap-south-1.temponest.com",
            grafana_url="http://grafana-ap-south-1.temponest.com",
            is_active=True,
            priority=1,
            data_residency=["IN", "SG", "AU"],
        ),
    },
    failover_enabled=True,
    health_check_interval=30,
    routing_strategy="latency",
)


class RegionRouter:
    """Routes requests to appropriate regions"""

    def __init__(self, config: MultiRegionConfig = DEFAULT_CONFIG):
        self.config = config
        self.region_health: Dict[str, bool] = {}
        self._initialize_health()

    def _initialize_health(self):
        """Initialize health status for all regions"""
        for region_code in self.config.regions:
            self.region_health[region_code] = True

    def get_region_for_tenant(
        self,
        tenant_id: str,
        tenant_country: Optional[str] = None,
    ) -> Optional[RegionConfig]:
        """
        Get the appropriate region for a tenant

        Args:
            tenant_id: Tenant identifier
            tenant_country: ISO country code for the tenant

        Returns:
            RegionConfig for the selected region
        """
        if not self.config.enabled:
            return self.config.regions.get(self.config.primary_region)

        # Check data residency requirements
        if tenant_country:
            for region_code, region in self.config.regions.items():
                if not region.is_active:
                    continue

                if tenant_country in region.data_residency:
                    if self.region_health.get(region_code, False):
                        return region

        # Fall back to routing strategy
        return self._route_by_strategy()

    def _route_by_strategy(self) -> Optional[RegionConfig]:
        """Route request based on configured strategy"""
        healthy_regions = [
            (code, region)
            for code, region in self.config.regions.items()
            if region.is_active and self.region_health.get(code, False)
        ]

        if not healthy_regions:
            # All regions unhealthy, return primary
            return self.config.regions.get(self.config.primary_region)

        if self.config.routing_strategy == "priority":
            # Sort by priority (higher first)
            healthy_regions.sort(key=lambda x: x[1].priority, reverse=True)
            return healthy_regions[0][1]

        elif self.config.routing_strategy == "round_robin":
            # Simple round-robin (in production, use Redis for distributed state)
            import random
            return random.choice(healthy_regions)[1]

        else:  # latency-based
            # In production, measure actual latency to each region
            # For now, use priority as proxy
            healthy_regions.sort(key=lambda x: x[1].priority, reverse=True)
            return healthy_regions[0][1]

    def get_failover_region(
        self,
        failed_region: str,
        exclude_regions: Optional[List[str]] = None,
    ) -> Optional[RegionConfig]:
        """
        Get a failover region when primary fails

        Args:
            failed_region: Region code that failed
            exclude_regions: Regions to exclude from failover

        Returns:
            RegionConfig for failover region
        """
        if not self.config.failover_enabled:
            return None

        exclude = set(exclude_regions or [])
        exclude.add(failed_region)

        healthy_regions = [
            (code, region)
            for code, region in self.config.regions.items()
            if (
                code not in exclude
                and region.is_active
                and self.region_health.get(code, False)
            )
        ]

        if not healthy_regions:
            return None

        # Sort by priority
        healthy_regions.sort(key=lambda x: x[1].priority, reverse=True)
        return healthy_regions[0][1]

    def update_region_health(self, region_code: str, is_healthy: bool):
        """Update health status for a region"""
        self.region_health[region_code] = is_healthy

    def get_all_regions(self) -> List[RegionConfig]:
        """Get all configured regions"""
        return list(self.config.regions.values())

    def get_healthy_regions(self) -> List[RegionConfig]:
        """Get all healthy and active regions"""
        return [
            region
            for code, region in self.config.regions.items()
            if region.is_active and self.region_health.get(code, False)
        ]


class DataResidencyChecker:
    """Ensures data residency compliance"""

    @staticmethod
    def check_compliance(
        user_country: str,
        region: RegionConfig,
    ) -> bool:
        """
        Check if storing data in region complies with user's country requirements

        Args:
            user_country: ISO country code of the user
            region: Target region

        Returns:
            True if compliant, False otherwise
        """
        # If no data residency requirements, allow any region
        if not region.data_residency:
            return True

        # Check if user's country is in allowed list
        return user_country in region.data_residency

    @staticmethod
    def get_compliant_regions(
        user_country: str,
        config: MultiRegionConfig,
    ) -> List[RegionConfig]:
        """Get all regions compliant with user's country"""
        compliant = []
        for region in config.regions.values():
            if DataResidencyChecker.check_compliance(user_country, region):
                compliant.append(region)
        return compliant


# Example usage in FastAPI middleware:
"""
from multi_region import RegionRouter, MultiRegionConfig

region_router = RegionRouter(config=MultiRegionConfig(...))

@app.middleware("http")
async def region_routing_middleware(request: Request, call_next):
    # Get tenant info from auth
    tenant_id = request.state.tenant_id
    tenant_country = request.state.tenant_country

    # Get appropriate region
    region = region_router.get_region_for_tenant(tenant_id, tenant_country)

    # Add region info to request state
    request.state.region = region

    # Forward request to regional service if needed
    if region.code != "local":
        # Proxy to regional service
        # ... implementation ...
        pass

    response = await call_next(request)
    return response
"""
