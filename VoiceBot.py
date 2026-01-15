# -*- coding: utf-8 -*-
"""
Created on Wed Jan 14 07:54:44 2026

Voice Bot using Google Search (updated from using speech_recognition)

#check the name of your microphone
import sounddevice as sd
print(sd.query_devices())

# Install libraries(if not already installed):
pip install openai-whisper playwright sounddevice scipy
pip install playwright
pip install chromium


#installed in anaconda prompt:
conda install -c conda-forge ffmpeg

microphone is identified by Windows as a "Microphone Array"
and is assigned to Device ID 1.


@author: Shannon Leigh Comeaux
"""
import nest_asyncio
nest_asyncio.apply()
import whisper
import pyaudio
import sounddevice as sd
from scipy.io.wavfile import write
from playwright.sync_api import sync_playwright
import os

class VoiceLinkSearch:
    def __init__(self):
        print("Loading Whisper Turbo...")
        self.model = whisper.load_model("turbo")
        self.start_listening()

    def record_and_transcribe(self, duration=4):
        fs, filename = 44100, "temp_voice.wav"
        # UPDATED: Use ID 1 and 4 channels based on your device list
        target_device = 1
        num_channels = 4

        print(f"\nListening on Device {target_device}...")
        try:
            # Record all 4 channels to ensure we capture the array signal
            recording = sd.rec(int(duration * fs), samplerate=fs, channels=num_channels, device=target_device)
            sd.wait()
        except Exception as e:
            print(f"Mic error: {e}. Trying default...")
            recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
            sd.wait()

        import numpy as np
        max_volume = np.max(np.abs(recording))
        print(f"Volume Level: {max_volume:.4f}")

    # FIX: If volume is 0, skip transcription to avoid "thank you" hallucinations
        if max_volume < 0.001:
            return ""

        write(filename, fs, recording)

    # Transcribe and fix the dictionary return error
        result = self.model.transcribe(filename, fp16=False)
        os.remove(filename)

        return result["text"].strip().lower() # Use ["text"] to get the string

    def start_listening(self):
        while True:
            # Increased duration to 5 seconds so you aren't rushed
            command = self.record_and_transcribe(duration=5)

            if not command or len(command) < 3:
                continue

            # 1. Filter out common Whisper hallucinations
            if command in ["thank you.", "thanks.", "thank you, sister.", "thanks for watching."]:
                print("Skipping hallucination...")
                continue

            print(f"Heard: {command}")

            # 2. Fuzzy Matching: Catch "zurch", "surch", "search", etc.
            search_keywords = ["search", "zurch", "surch", "find", "open"]

            # Check if any keyword is in the command
            found_keyword = next((kw for kw in search_keywords if kw in command), None)

            if found_keyword:
                # Extract everything after the keyword
                query = command.split(found_keyword)[-1].strip()

                # 3. Handle cases where it only heard the keyword
                if len(query) > 1:
                    print(f"Action: Searching Google for '{query}'")
                    self.find_and_open_link(query)
                else:
                    print("Status: I heard the command but missed the topic. Try again.")

            elif "stop" in command or "exit" in command:
                print("Stopping...")
                break





    def find_and_open_link(self, query):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()
            page.goto(f"www.google.com{query}")


            try:
                # Wait for the main result headers (h3) to appear
                page.wait_for_selector("h3")
                page.locator("a > h3").first.click()

                print(f"Opened top result for: {query}")
                page.wait_for_timeout(10000)
                '''
                # 2026 selector: Get the first link wrapping the first h3 result
                # This ignores ads and finds the first organic site
                first_link = page.locator("h3").first.locator("xpath=..")
                site_url = first_link.get_attribute("href")

                print(f"Found site: {site_url}")
                page.goto(site_url)

                page.wait_for_timeout(10000) # Stay on the site for 10 seconds
            '''
            except Exception as e:
                print(f"Could not find a link: {e}")
            finally:

                browser.close()

if __name__ == "__main__":
    VoiceLinkSearch()
