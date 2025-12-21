"""
Quick setup script to verify MCP Python client installation and configuration
"""
import sys

def check_mcp_installation():
    """Check if MCP Python SDK is installed"""
    try:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
        print("✅ MCP Python SDK is installed")
        return True
    except ImportError as e:
        print(f"❌ MCP Python SDK not found: {e}")
        print("\nTo install, run:")
        print("  pip install mcp")
        return False

def check_docker():
    """Check if Docker is available"""
    import subprocess
    try:
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"✅ Docker is available: {result.stdout.strip()}")
            return True
        else:
            print("❌ Docker command failed")
            return False
    except FileNotFoundError:
        print("❌ Docker not found. Please install Docker Desktop or Docker Engine")
        return False
    except Exception as e:
        print(f"❌ Error checking Docker: {e}")
        return False

def check_chembl_image():
    """Check if chembl-mcp-server Docker image exists"""
    import subprocess
    try:
        result = subprocess.run(
            ["docker", "images", "chembl-mcp-server"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if "chembl-mcp-server" in result.stdout:
            print("✅ chembl-mcp-server Docker image found")
            return True
        else:
            print("⚠️  chembl-mcp-server Docker image not found")
            print("   The image will be pulled automatically when first used")
            return False
    except Exception as e:
        print(f"⚠️  Could not check for Docker image: {e}")
        return False

def main():
    print("MCP Python Client Setup Check\n")
    print("=" * 50)
    
    mcp_ok = check_mcp_installation()
    docker_ok = check_docker()
    image_ok = check_chembl_image()
    
    print("\n" + "=" * 50)
    if mcp_ok and docker_ok:
        print("\n✅ Setup looks good! You can run the Streamlit app.")
        if not image_ok:
            print("⚠️  Note: The Docker image will be pulled on first use.")
    else:
        print("\n❌ Setup incomplete. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()

