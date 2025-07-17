import asyncio
import logging
import subprocess
import time
from typing import Any, List, Optional

import aiohttp

logger = logging.getLogger(__name__)


class ContainerOrchestrator:
    def __init__(self, compose_file_path: str):
        self.compose_file_path = compose_file_path

    def _run_compose_command(self, command: List[str], profile: Optional[str] = None) -> str:
        cmd = ["podman", "compose", "-f", self.compose_file_path]
        if profile:
            cmd.extend(["--profile", profile])
        cmd.extend(command)

        logger.info(f"Running compose command: {' '.join(cmd)}")

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.debug(f"Compose stdout: {result.stdout}")
            if result.stderr:
                logger.warning(f"Compose stderr: {result.stderr}")
            return result.stdout
        except subprocess.CalledProcessError as e:
            logger.error(f"Compose command failed: {e.cmd}")
            logger.error(f"Stdout: {e.stdout}")
            logger.error(f"Stderr: {e.stderr}")
            raise

    def up(self, profile: Optional[str] = None, build: bool = False) -> None:
        command = ["up", "-d"]
        if build:
            command.append("--build")
        self._run_compose_command(command, profile=profile)
        logger.info(f"Containers for profile '{profile or 'default'}' started.")

    def down(self, profile: Optional[str] = None) -> None:
        self._run_compose_command(["down"], profile=profile)
        logger.info(f"Containers for profile '{profile or 'default'}' stopped and removed.")

    def build_images(self) -> None:
        self._run_compose_command(["build"])
        logger.info("All images built.")

    async def check_instance_health(self, session: aiohttp.ClientSession, instance_url: str, model_name: str) -> bool:
        """Check if an Ollama instance is ready and has the model loaded"""
        try:
            async with session.get(f"{instance_url}/api/version", timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    async with session.get(
                        f"{instance_url}/api/tags",
                        timeout=aiohttp.ClientTimeout(total=5),
                    ) as tags_response:
                        if tags_response.status == 200:
                            tags_data = await tags_response.json()
                            models = [m["name"] for m in tags_data.get("models", [])]
                            return model_name in models
                return False
        except Exception as e:
            logger.debug(f"Health check failed for {instance_url}: {e}")
            return False

    async def wait_for_instances(self, instances: List[Any], max_wait: int = 300) -> List[Any]:
        """Wait for all Ollama instances to be ready and models loaded"""
        logger.info(f"Waiting for {len(instances)} Ollama instances to be ready...")

        async with aiohttp.ClientSession() as session:
            start_time = time.time()

            while time.time() - start_time < max_wait:
                health_tasks = []
                for inst in instances:
                    # Assuming inst is a ModelInstance object with .url and .model attributes
                    health_tasks.append(self.check_instance_health(session, inst.url, inst.model))

                health_results = await asyncio.gather(*health_tasks, return_exceptions=True)

                current_ready_instances = []
                for i, inst in enumerate(instances):
                    if isinstance(health_results[i], bool) and health_results[i]:
                        current_ready_instances.append(inst)

                if len(current_ready_instances) == len(instances):
                    logger.info(f"All {len(instances)} instances are ready: {[inst.name for inst in instances]}")
                    return instances

                ready_names = [inst.name for inst in current_ready_instances]
                not_ready_names = [inst.name for inst in instances if inst not in current_ready_instances]

                if ready_names:
                    logger.info(f"Ready: {ready_names}")
                if not_ready_names:
                    logger.info(f"Not ready: {not_ready_names}")

                await asyncio.sleep(10)

            logger.warning(f"Not all Ollama instances are ready after {max_wait}s.")
            return [inst for inst in instances if inst in current_ready_instances]  # Return whatever is ready

    def get_service_ports(self, service_name: str) -> List[int]:
        # This is a simplified approach. A more robust solution would parse
        # `docker compose port` output or inspect containers directly. For now,
        # we rely on known ports from docker-compose.yml. This method might need
        # refinement if port mapping becomes dynamic.
        if service_name == "ollama-small":
            return [11434]
        elif service_name == "ollama-medium":
            return [11435]
        elif service_name == "ollama-large":
            return [11436]
        elif service_name == "ollama-code":
            return [11437]
        return []
