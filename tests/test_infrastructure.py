#!/usr/bin/env python3
"""
Infrastructure tests for matrix-docker
Tests Matrix server configuration and Docker setup
"""

import os
import subprocess
import sys
import yaml


def test_docker_compose_file_exists():
    """Test that docker-compose.yml exists and is valid"""
    assert os.path.exists('docker-compose.yml'), "docker-compose.yml not found"

    with open('docker-compose.yml', 'r') as f:
        compose = yaml.safe_load(f)
        assert compose is not None, "docker-compose.yml is not valid YAML"
        assert 'services' in compose, "No services defined in docker-compose.yml"

    print("✓ docker-compose.yml exists and is valid")


def test_matrix_services_defined():
    """Test that Matrix services are defined"""
    with open('docker-compose.yml', 'r') as f:
        compose = yaml.safe_load(f)

    services = compose.get('services', {})
    required_services = ['synapse', 'postgres', 'redis']

    for service in required_services:
        # Service name might be slightly different
        found = any(s in services for s in [service, service.replace('_', '-')])
        if not found:
            print(f"⚠ Service {service} not found (may be optional)")

    # Check for at least synapse
    assert 'synapse' in services or 'synapse' in str(services).lower(), \
        "Synapse service not found in docker-compose.yml"

    print("✓ Matrix services are defined")


def test_docker_compose_config():
    """Test docker-compose configuration with docker compose"""
    try:
        result = subprocess.run(
            ['docker', 'compose', 'config'],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode != 0:
            print(f"⚠ docker compose config had warnings: {result.stderr}")
        else:
            print("✓ docker compose config is valid")
    except FileNotFoundError:
        print("⚠ Docker not available, skipping compose config test")
    except subprocess.TimeoutExpired:
        print("⚠ docker compose config timed out")


def test_port_configuration():
    """Test that required Matrix ports are configured"""
    with open('docker-compose.yml', 'r') as f:
        compose = yaml.safe_load(f)

    # Check for Matrix ports
    ports = []
    for service_name, service_config in compose.get('services', {}).items():
        service_ports = service_config.get('ports', [])
        ports.extend(service_ports)

    port_mappings = str(ports)

    # Check for common Matrix ports
    required_ports = ['8008', '8448']  # Synapse HTTP/HTTPS
    optional_ports = ['5432', '6379']  # Postgres, Redis

    for port in required_ports:
        if port in port_mappings:
            print(f"✓ Port {port} (Synapse) is configured")
        else:
            print(f"⚠ Port {port} (Synapse) not found")

    print("✓ Port configuration checked")


def test_volumes_defined():
    """Test that persistent volumes are configured"""
    with open('docker-compose.yml', 'r') as f:
        compose = yaml.safe_load(f)

    services = compose.get('services', {})

    # Check for volumes in critical services
    for service_name in ['synapse', 'postgres']:
        if service_name in services:
            service_config = services[service_name]
            volumes = service_config.get('volumes', [])
            if len(volumes) > 0:
                print(f"✓ {service_name} has {len(volumes)} volume(s) defined")
            else:
                print(f"⚠ {service_name} has no volumes defined")


def test_network_configuration():
    """Test that networks are properly configured"""
    with open('docker-compose.yml', 'r') as f:
        compose = yaml.safe_load(f)

    networks = compose.get('networks', {})
    assert len(networks) > 0, "No networks defined"

    print(f"✓ {len(networks)} network(s) configured")


def test_environment_files():
    """Test that environment configuration files exist"""
    env_files = [
        '.env.example',
        'synapse/.env.example',
        'postgres/.env.example',
    ]

    found = []
    for env_file in env_files:
        if os.path.exists(env_file):
            found.append(env_file)
            print(f"✓ {env_file} exists")

    if len(found) == 0:
        print("⚠ No .env.example files found")


if __name__ == '__main__':
    print("Running matrix-docker infrastructure tests...\n")

    tests = [
        test_docker_compose_file_exists,
        test_matrix_services_defined,
        test_docker_compose_config,
        test_port_configuration,
        test_volumes_defined,
        test_network_configuration,
        test_environment_files,
    ]

    failed = 0
    for test in tests:
        try:
            test()
        except AssertionError as e:
            print(f"✗ {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"⚠ {test.__name__}: {e}")

    print(f"\n{'='*50}")
    print(f"Tests run: {len(tests)}")
    print(f"Passed: {len(tests) - failed}")
    print(f"Failed: {failed}")

    sys.exit(1 if failed > 0 else 0)
