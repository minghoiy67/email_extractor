import re
import requests
from bs4 import BeautifulSoup
from itertools import product  # For generating combinations
import threading  # For handling timeout
import sys
import time  # For adding delays between requests

def load_keywords(file_path):
    """Load keywords from a file."""
    try:
        with open(file_path, 'r', encoding="utf-8") as file:  # Ensure utf-8 encoding
            return [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        return []

def extract_urls_from_page(url):
    """Extract URLs from a web page."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Debug: Save the fetched HTML to a file for inspection
        with open("debug_fetched_page.html", "w", encoding="utf-8") as debug_file:
            debug_file.write(soup.prettify())
        print("Fetched HTML content saved to 'debug_fetched_page.html'")  # Debug log

        # Extract URLs from the page
        links = []
        raw_links = [a['href'] for a in soup.find_all('a', href=True)]  # Extract all href attributes
        print(f"Raw links extracted: {raw_links}")  # Debug log

        # Filter valid links
        valid_links = [href for href in raw_links if href.startswith("http")]
        print(f"Valid links after filtering: {valid_links}")  # Debug log

        return valid_links
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL '{url}': {e}")
        return []
    except Exception as e:
        print(f"Unexpected error while extracting URLs: {e}")
        return []

def generate_keywords(base_words, max_combinations=1000):
    """Generate expanded keywords from a list of base words."""
    prefixes = ["best", "top", "latest", "find", "search", "buy", "cheap"]
    suffixes = ["review", "guide", "price", "near me", "online", "2023"]
    generated_keywords = set()

    # Generate combinations of base words with prefixes and suffixes
    for word in base_words:
        generated_keywords.add(word)  # Include the base word itself
        for prefix in prefixes:
            generated_keywords.add(f"{prefix} {word}")
        for suffix in suffixes:
            generated_keywords.add(f"{word} {suffix}")
        for prefix, suffix in product(prefixes, suffixes):
            generated_keywords.add(f"{prefix} {word} {suffix}")
            if len(generated_keywords) >= max_combinations:
                print("Reached maximum keyword combinations. Stopping generation.")
                break
        if len(generated_keywords) >= max_combinations:
            break

    print(f"Generated {len(generated_keywords)} keywords.")  # Debug log
    return list(generated_keywords)

def extract_emails_from_page(url):
    """Extract emails from a web page."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        page_content = response.text

        # Use regex to find email addresses in the page content
        email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        emails = re.findall(email_pattern, page_content)
        unique_emails = set(emails)  # Remove duplicates

        if unique_emails:
            print(f"Extracted emails from {url}: {unique_emails}")  # Debug log
        else:
            print(f"No emails found on the page: {url}")  # Notify if no emails are found
        return unique_emails
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL '{url}' for email extraction: {e}")
        return set()
    except Exception as e:
        print(f"Unexpected error while extracting emails from {url}: {e}")
        return set()

def save_emails_to_file(emails, file_path="emails.txt"):
    """Save emails to a file in real-time, avoiding duplicates."""
    try:
        existing_emails = set()
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                existing_emails = {line.strip() for line in file if line.strip()}
        except FileNotFoundError:
            pass  # If the file doesn't exist, proceed with saving new emails

        new_emails = emails - existing_emails  # Avoid duplicates
        if new_emails:
            with open(file_path, "a", encoding="utf-8") as file:  # Open in append mode
                for email in new_emails:
                    file.write(email + "\n")
            print(f"Saved {len(new_emails)} new emails to {file_path}.")
        else:
            print("No new emails to save.")
    except IOError as e:
        print(f"Error writing to file '{file_path}': {e}")

def process_url_and_extract_emails(url):
    """Process a single URL to extract and save emails."""
    print(f"Processing URL for email extraction: {url}")  # Notify the start of email extraction
    emails = extract_emails_from_page(url)
    if emails:
        save_emails_to_file(emails)
    else:
        print(f"No emails extracted from {url}. This could be due to a lack of emails on the page or a search issue.")

def search_urls(keywords):
    """Search for URLs containing the given keywords and extract emails."""
    urls = set()  # Use a set to avoid duplicate URLs
    exclude_keywords = [
        "info", "news", "support", "contact", ".edu", ".gov", "privacy",
        "frontdesk", "help", ".png", "school", "customerservices",
        "firstname", "compliance", "career", "example", "feedback",
        "subscriptions", "customercare", "editor", "questions",
        "contact us", "forum", "download", "login", "signup"
    ]
    try:
        with open("urls.txt", "w", encoding="utf-8") as output_file:  # Specify utf-8 encoding
            for keyword in keywords:
                print(f"Searching for URLs with keyword: {keyword}...")
                search_url = f"https://www.bing.com/search?q={keyword}"
                
                # Retry mechanism for blocked requests
                for attempt in range(3):  # Retry up to 3 times
                    fetched_urls = extract_urls_from_page(search_url)
                    if fetched_urls:
                        break
                    print(f"Retrying ({attempt + 1}/3) for keyword: {keyword}...")  # Debug log

                if not fetched_urls:
                    print(f"No URLs fetched for keyword: {keyword}")
                    continue

                print(f"Fetched URLs for keyword '{keyword}': {fetched_urls}")  # Debug log

                filtered_urls = [
                    url for url in fetched_urls
                    if not any(exclude in url.lower() for exclude in exclude_keywords)
                ]
                if not filtered_urls:
                    print(f"No filtered URLs for keyword: {keyword}")
                    continue

                print(f"Filtered URLs for keyword '{keyword}': {filtered_urls}")  # Debug log

                for url in filtered_urls:
                    if url not in urls:  # Avoid duplicates
                        output_file.write(url + "\n")  # Save URL in real-time
                        output_file.flush()  # Ensure the URL is written immediately
                        urls.add(url)  # Add the URL to the set
                        print(f"URL saved: {url}")  # Debug log

                        # Extract emails from the URL immediately
                        process_url_and_extract_emails(url)

                        # Add a delay to avoid overwhelming the server
                        time.sleep(2)
                print(f"Found {len(filtered_urls)} URLs for keyword: {keyword}")
    except IOError as e:
        print(f"Error writing to file: {e}")
    return list(urls)  # Convert the set back to a list for the return value

def append_keywords_to_file(file_path, keywords):
    """Append keywords to a file without overwriting existing content."""
    try:
        with open(file_path, "a", encoding="utf-8") as file:  # Open in append mode
            for keyword in keywords:
                file.write(keyword + "\n")
        print(f"Appended {len(keywords)} keywords to {file_path}.")
    except IOError as e:
        print(f"Error writing to file '{file_path}': {e}")

def prompt_for_keywords():
    """Prompt the user to generate more keywords."""
    response = input("Do you want to generate more keywords? (yes/no): ").strip().lower()
    if response == "yes":
        user_input = input("Enter your keyword(s), separated by commas: ").strip()
        base_words = [word.strip() for word in user_input.split(",") if word.strip()]
        if base_words:
            generated_keywords = generate_keywords(base_words)
            append_keywords_to_file("keywords.txt", generated_keywords)
        else:
            print("No valid keywords entered. Skipping keyword generation.")
    elif response == "no":
        print("Skipping keyword generation.")
    else:
        print("Invalid response. Skipping keyword generation.")

def load_words_from_file(file_path):
    """Load words from a file."""
    try:
        with open(file_path, 'r', encoding="utf-8") as file:
            return [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        return []

def overwrite_keywords(file_path, keywords):
    """Overwrite keywords in a file."""
    try:
        with open(file_path, "w", encoding="utf-8") as file:  # Open in write mode
            for keyword in keywords:
                file.write(keyword + "\n")
        print(f"Overwritten {len(keywords)} keywords in {file_path}.")
    except IOError as e:
        print(f"Error writing to file '{file_path}': {e}")

def remove_used_keyword(file_path, keyword):
    """Remove a used keyword from the file."""
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            keywords = [line.strip() for line in file if line.strip()]
        keywords = [k for k in keywords if k != keyword]  # Remove the used keyword
        with open(file_path, "w", encoding="utf-8") as file:
            for k in keywords:
                file.write(k + "\n")
        print(f"Removed used keyword '{keyword}' from {file_path}.")
    except IOError as e:
        print(f"Error updating file '{file_path}': {e}")

def process_next_keyword_from_ind():
    """Process the next keyword from IND.txt."""
    ind_keywords = load_words_from_file("IND.txt")
    if not ind_keywords:
        print("No keywords left in IND.txt. Stopping the process.")
        return None
    next_keyword = ind_keywords[0]  # Take the first keyword
    print(f"Using keyword '{next_keyword}' from IND.txt to generate new keywords...")
    generated_keywords = generate_keywords([next_keyword])
    overwrite_keywords("keywords.txt", generated_keywords)  # Overwrite keywords.txt
    remove_used_keyword("IND.txt", next_keyword)  # Remove the used keyword
    return next_keyword

def prompt_for_keywords_with_timeout():
    """Prompt the user to generate new keywords with a timeout."""
    def timeout_input(prompt, timeout):
        """Prompt for input with a timeout."""
        result = [None]

        def get_input():
            try:
                result[0] = input(prompt)
            except EOFError:
                result[0] = None

        thread = threading.Thread(target=get_input)
        thread.daemon = True
        thread.start()
        thread.join(timeout)
        if thread.is_alive():
            print("\nNo response received within the timeout period.")
            return None
        return result[0]

    response = timeout_input("Do you want to generate new keywords? (yes/no/stop): ", 20)
    if response is None or response.strip().lower() not in ["yes", "no", "stop"]:
        return process_next_keyword_from_ind()
    elif response.strip().lower() == "yes":
        user_input = input("Enter your keyword(s), separated by commas: ").strip()
        base_words = [word.strip() for word in user_input.split(",") if word.strip()]
        if base_words:
            generated_keywords = generate_keywords(base_words)
            overwrite_keywords("keywords.txt", generated_keywords)
        else:
            print("No valid keywords entered. Skipping keyword generation.")
        return None
    elif response.strip().lower() == "no":
        print("Skipping keyword generation.")
        return None
    elif response.strip().lower() == "stop":
        print("Stopping the process as requested by the user.")
        sys.exit(0)  # Exit the script gracefully

def continuous_keyword_processing():
    """Continuously process keywords and search for URLs until stopped."""
    while True:
        # Load keywords from keywords.txt
        keywords_file = "keywords.txt"
        base_keywords = load_keywords(keywords_file)

        if base_keywords:
            # Generate expanded keywords with a limit on combinations
            keywords = generate_keywords(base_keywords, max_combinations=1000)

            # Use the keywords to search for URLs
            urls = search_urls(keywords)

            # Print the total number of saved URLs
            print(f"Total URLs saved: {len(urls)}")

            # Print the found URLs
            for url in urls:
                print(url)

            # Prompt the user again after finishing
            next_keyword = prompt_for_keywords_with_timeout()
            if next_keyword is None and not load_words_from_file("IND.txt"):
                print("No more keywords to process. Stopping.")
                break
        else:
            print("No keywords to process.")
            break  # Exit the loop if no keywords are found

# Prompt the user for keyword generation
prompt_for_keywords()

# Start the continuous keyword processing
continuous_keyword_processing()
