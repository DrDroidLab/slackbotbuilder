#!/usr/bin/env python3
"""
Setup script for Slack credentials
This script helps you configure your Slack app credentials in the YAML file.
"""

import os
import yaml
from slack_utils.slack_credentials_manager import credentials_manager

def setup_credentials():
    """Interactive setup for Slack credentials"""
    print("=== Slack Bot Credentials Setup ===\n")
    
    # Check if credentials file exists
    if os.path.exists("credentials.yaml"):
        print("Found existing credentials.yaml file")
        response = input("Do you want to update it? (y/n): ").lower().strip()
        if response != 'y':
            print("Setup cancelled.")
            return
    
    print("\nPlease provide your Slack app credentials:")
    print("(You can find these in your Slack app settings at https://api.slack.com/apps)")
    print()
    
    # Get credentials from user
    app_id = input("App ID: ").strip()
    signing_secret = input("Signing Secret: ").strip()
    bot_token = input("Bot User OAuth Token (starts with xoxb-): ").strip()
    
    # Validate inputs
    if not app_id or not signing_secret or not bot_token:
        print("\nError: All fields are required!")
        return
    
    if not bot_token.startswith("xoxb-"):
        print("\nWarning: Bot token should start with 'xoxb-'")
        response = input("Continue anyway? (y/n): ").lower().strip()
        if response != 'y':
            return
    
    # Create credentials structure
    credentials = {
        "slack": {
            "app_id": app_id,
            "signing_secret": signing_secret,
            "bot_token": bot_token
        },
        "api": {
            "base_url": "https://slack.com/api",
            "timeout": 30
        }
    }
    
    # Write to file
    try:
        with open("credentials.yaml", "w") as file:
            yaml.dump(credentials, file, default_flow_style=False, indent=2)
        
        print(f"\n✅ Credentials saved to credentials.yaml")
        
        # Validate the credentials
        credentials_manager.reload_credentials()
        if credentials_manager.validate_credentials():
            print("✅ Credentials are valid!")
        else:
            print("⚠️  Credentials may have issues. Please check the values.")
        
        print("\nNext steps:")
        print("1. Configure your Slack app with the webhook URLs")
        print("2. Install the app to your workspace")
        print("3. Run the bot with: python app.py")
        
    except Exception as e:
        print(f"\n❌ Error saving credentials: {e}")

def validate_current_credentials():
    """Validate current credentials"""
    print("=== Validating Current Credentials ===\n")
    
    if not os.path.exists("credentials.yaml"):
        print("❌ No credentials file found. Run setup first.")
        return
    
    credentials_manager.reload_credentials()
    summary = credentials_manager.get_credentials_summary()
    
    print("Credentials Summary:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    if credentials_manager.validate_credentials():
        print("\n✅ Credentials are valid!")
    else:
        print("\n❌ Credentials have issues. Please check the values.")

def main():
    """Main function"""
    print("Slack Bot Credentials Manager\n")
    
    while True:
        print("Options:")
        print("1. Setup new credentials")
        print("2. Validate current credentials")
        print("3. Exit")
        
        choice = input("\nSelect an option (1-3): ").strip()
        
        if choice == "1":
            setup_credentials()
        elif choice == "2":
            validate_current_credentials()
        elif choice == "3":
            print("Goodbye!")
            break
        else:
            print("Invalid option. Please try again.")
        
        print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    main() 