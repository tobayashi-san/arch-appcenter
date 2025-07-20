"""
Configuration Manager - Simplified
Handles GitHub config download and local caching
"""

import requests
import os
import yaml
import hashlib
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class ConfigItem:
    """Single configuration item"""
    name: str
    description: str
    command: str
    category: str = ""
    tags: List[str] = None
    requires: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.requires is None:
            self.requires = []

@dataclass
class ConfigCategory:
    """Configuration category with items"""
    id: str
    name: str
    description: str = ""
    items: List[ConfigItem] = None
    order: int = 999
    icon: str = ""

    def __post_init__(self):
        if self.items is None:
            self.items = []

class ConfigManager:
    def __init__(self, github_url: str = None, cache_path: str = "data/config_cache.yaml"):
        self.github_url = github_url or "https://raw.githubusercontent.com/tobayashi-san/arch-helper-tool/refs/heads/main/config.yaml"
        self.cache_path = cache_path
        self.cache_max_age = timedelta(hours=24)

        # Ensure data directory exists
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)

        self.config_data: Dict[str, ConfigCategory] = {}

    def is_cache_valid(self) -> bool:
        """Check if cached config is still valid"""
        if not os.path.exists(self.cache_path):
            return False

        try:
            cache_mtime = datetime.fromtimestamp(os.path.getmtime(self.cache_path))
            return datetime.now() - cache_mtime < self.cache_max_age
        except:
            return False

    def download_config(self) -> Optional[str]:
        """Download configuration from GitHub"""
        print(f"📥 Downloading config from GitHub...")

        try:
            headers = {'User-Agent': 'Arch-Config-Tool/2.0'}
            response = requests.get(self.github_url, headers=headers, timeout=30)
            response.raise_for_status()

            config_content = response.text
            if not config_content.strip():
                raise ValueError("Empty configuration file")

            # Validate YAML
            yaml.safe_load(config_content)

            # Save to cache
            with open(self.cache_path, 'w', encoding='utf-8') as f:
                f.write(config_content)

            print("✅ Configuration downloaded successfully")
            return config_content

        except Exception as e:
            print(f"❌ Download failed: {e}")
            return None

    def load_cached_config(self) -> Optional[str]:
        """Load configuration from local cache"""
        try:
            if os.path.exists(self.cache_path):
                with open(self.cache_path, 'r', encoding='utf-8') as f:
                    return f.read()
        except Exception as e:
            print(f"❌ Cache load failed: {e}")
        return None

    def parse_config(self, config_text: str) -> Dict[str, ConfigCategory]:
        """Parse YAML configuration into structured data"""
        try:
            config_data = yaml.safe_load(config_text)
            if not isinstance(config_data, dict):
                return {}

            categories = {}
            categories_data = config_data.get('categories', {})

            for category_id, category_info in categories_data.items():
                if not isinstance(category_info, dict):
                    continue

                # Create category
                category = ConfigCategory(
                    id=category_id,
                    name=category_info.get('name', category_id.replace('_', ' ').title()),
                    description=category_info.get('description', ''),
                    order=category_info.get('order', 999),
                    icon=category_info.get('icon', ''),
                    items=[]
                )

                # Parse tools
                tools = category_info.get('tools', [])
                for tool_info in tools:
                    if not isinstance(tool_info, dict):
                        continue

                    # Required fields
                    name = tool_info.get('name', '').strip()
                    description = tool_info.get('description', '').strip()
                    command = tool_info.get('command', '').strip()

                    if not all([name, description, command]):
                        continue

                    # Create config item
                    config_item = ConfigItem(
                        name=name,
                        description=description,
                        command=command,
                        category=category_id,
                        tags=tool_info.get('tags', []),
                        requires=tool_info.get('requires', [])
                    )

                    category.items.append(config_item)

                # Sort items by name
                category.items.sort(key=lambda item: item.name)
                categories[category_id] = category

            print(f"✅ Parsed {len(categories)} categories with {sum(len(cat.items) for cat in categories.values())} tools")
            return categories

        except Exception as e:
            print(f"❌ Parse failed: {e}")
            return {}

    def get_config(self, force_update: bool = False) -> Dict[str, ConfigCategory]:
        """Get configuration (from cache or download)"""
        config_content = None

        # Check if update is needed
        if force_update or not self.is_cache_valid():
            config_content = self.download_config()

        # Fallback to cache if download failed
        if not config_content:
            config_content = self.load_cached_config()

        # Parse configuration
        if config_content:
            self.config_data = self.parse_config(config_content)
            return self.config_data
        else:
            print("❌ No configuration available!")
            return {}

    def get_categories(self) -> List[ConfigCategory]:
        """Get sorted list of categories"""
        if not self.config_data:
            self.get_config()

        categories = list(self.config_data.values())
        categories.sort(key=lambda cat: cat.order)
        return categories

    def get_category_items(self, category_id: str) -> List[ConfigItem]:
        """Get items for specific category"""
        if not self.config_data:
            self.get_config()

        category = self.config_data.get(category_id)
        return category.items if category else []

    def search_tools(self, search_term: str) -> List[ConfigItem]:
        """Search for tools by name or description"""
        if not self.config_data:
            self.get_config()

        search_term = search_term.lower()
        results = []

        for category in self.config_data.values():
            for item in category.items:
                if (search_term in item.name.lower() or
                    search_term in item.description.lower() or
                    any(search_term in tag.lower() for tag in item.tags)):
                    results.append(item)

        return results
