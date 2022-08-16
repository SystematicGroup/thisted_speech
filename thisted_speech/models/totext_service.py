import os
from time import sleep, time

from google.cloud import speech

import pyaudio
import queue
import wave

from loguru import logger

# Audio recording parameters
from thisted_speech.app.core.config import INPUT_FILENAME

RATE = 16000
CHUNK = int(RATE / 10)  # 100ms


class MicrophoneStream:
    """Opens a recording stream as a generator yielding the audio chunks."""

    def __init__(self, rate, chunk, filename=None):
        self._filename = filename
        self._wf = None
        self._chunk = chunk
        self._audio_interface = None
        self._audio_stream = None
        self._audio_interface_format = None
        self._nchannels = None
        self.speech_format = None
        self.speech_rate = rate
        # Create a thread-safe buffer of audio data
        self._buff = queue.Queue()
        self.closed = True

        self._recorded_frames = []

    def open(self):
        self._audio_interface_format = pyaudio.paInt16
        self._nchannels = 1
        self._audio_interface = pyaudio.PyAudio()
        if self._filename is not None:
            self._wf = wave.open(self._filename, "rb")
            self._audio_interface_format = self._audio_interface.get_format_from_width(self._wf.getsampwidth())
            self._nchannels = self._wf.getnchannels()
            self.speech_rate = self._wf.getframerate()

        if self._audio_interface_format == pyaudio.paInt16:
            self.speech_format = speech.RecognitionConfig.AudioEncoding.LINEAR16
        else:
            raise Exception("got unexpected format {}".format(self._audio_interface_format))

        if self._filename is None:
            self._audio_stream = self._audio_interface.open(
                format=self._audio_interface_format,
                channels=self._nchannels,
                rate=self.speech_rate,
                input=True,
                frames_per_buffer=self._chunk,
                # Run the audio stream asynchronously to fill the buffer object.
                # This is necessary so that the input device's buffer doesn't
                # overflow while the calling thread makes network requests, etc.
                stream_callback=self._fill_buffer
            )

        else:
            self._audio_stream = self._audio_interface.open(
                format=self._audio_interface_format,
                channels=self._nchannels,
                rate=self.speech_rate,
                output=True,
                frames_per_buffer=self._chunk,
                # Run the audio stream asynchronously to fill the buffer object.
                # This is necessary so that the input device's buffer doesn't
                # overflow while the calling thread makes network requests, etc.
                stream_callback=self._fill_buffer
            )
        self.closed = False

    def __enter__(self):
        self.open()
        return self

    def close(self, user_name):
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        # Signal the generator to terminate so that the client's
        # streaming_recognize method will not block the process termination.
        self._buff.put(None)
        self._audio_interface.terminate()

        if user_name is not None:
            sound_folder = "sound-files"
            save_label = sound_folder + "/" + user_name + "_" + str(time()) + ".wav"
            logger.info("current dir {}".format(os.getcwd()))
            if not os.path.exists(os.path.join(os.getcwd(), sound_folder)):
                logger.info("creating sound_folder")
                os.makedirs(sound_folder)
            logger.info(save_label)
            wave_file = wave.open(save_label, 'wb')
            wave_file.setnchannels(self._nchannels)
            wave_file.setsampwidth(self._audio_interface.get_sample_size(self._audio_interface_format))
            wave_file.setframerate(self.speech_rate)
            wave_file.writeframes(b''.join(self._recorded_frames))
            wave_file.close()
            logger.info("Sound file saved under {}".format(save_label))

    def __exit__(self, type, value, traceback):
        self.close(user_name=None)

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        """Continuously collect data from the audio stream, into the buffer."""
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self):
        while not self.closed:
            # Use a blocking get() to ensure there's at least one chunk of
            # data, and stop iteration if the chunk is None, indicating the
            # end of the audio stream.
            chunk = self._buff.get()
            if chunk is None:
                return
            data = [chunk]

            self._recorded_frames.append(chunk)

            # Now consume whatever other data's still buffered.
            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        return
                    # print("mic: got data")
                    data.append(chunk)
                except queue.Empty:
                    break

            yield b"".join(data)


class CurrentStateModel:
    def __init__(self):
        self.init()

    def init(self):
        self.full_text = ""
        self.current_sentence = ""
        self.totext_stream = None
        self.client = None
        self.config = None
        self.streaming_config = None
        self.requests = None
        self.responses = None


current_state_model = CurrentStateModel()  # for debugging


def open_stream(current_state: CurrentStateModel, rate=RATE, chunk=CHUNK):
    print("opening mic/file stream")
    current_state.init()
    language_code = "da-DK"  
    current_state.totext_stream = MicrophoneStream(rate, chunk, filename=INPUT_FILENAME)
    current_state.totext_stream.open()
    current_state.client = speech.SpeechClient()
    current_state.config = speech.RecognitionConfig(encoding=current_state.totext_stream.speech_format,
                                                    sample_rate_hertz=current_state.totext_stream.speech_rate,
                                                    language_code=language_code,
                                                    speech_contexts=[{'phrases' :
                                                                          ['sosu medarbejder', 'stop', '$TIME',
                                                                           '$ORDINAL', '$DAY']}]
                                                    )

    current_state.streaming_config = speech.StreamingRecognitionConfig(
        config=current_state.config, interim_results=True
    )

    audio_generator = current_state.totext_stream.generator()
    current_state.requests = (
        speech.StreamingRecognizeRequest(audio_content=content)
        for content in audio_generator
    )  # note this creates a generator

    current_state.responses = None


def get_next(current_state: CurrentStateModel) -> (bool, str):
    print("in get_next")
    if current_state.client is None:
        sleep(0.1)
        return True, ""

    if current_state.responses is None:
        print("setup google stream")
        current_state.responses = current_state.client.streaming_recognize(current_state.streaming_config,
                                                                           current_state.requests)

    print("starting loop")
    for response in current_state.responses:
        print("got something")
        if not response.results:
            sleep(0.1)
            continue

        # The `results` list is consecutive. For streaming, we only care about
        # the first result being considered, since once it's `is_final`, it
        # moves on to considering the next utterance.
        result = response.results[0]
        if not result.alternatives:
            sleep(0.1)
            continue

        # Display the transcription of the top alternative.
        transcript = result.alternatives[0].transcript
        print(result.is_final, transcript)
        if result.is_final:
            current_state.full_text += transcript
            current_state.current_sentence = ""
        else:
            current_state.current_sentence = transcript
            if current_state.current_sentence == "":
                sleep(0.1)
                continue
        return result.is_final, current_state.full_text + current_state.current_sentence

    print("no data in responses")
    sleep(0.1)
    return True, ""


def close_stream(current_state: CurrentStateModel, user_name: str):
    current_state.totext_stream.close(user_name)
    # we could reset current_state but keep it for debugging


if __name__ == "__main__":
    proot = os.path.abspath(os.path.dirname(__file__))
    proot = os.path.abspath(os.path.join(proot, "..", ".."))
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "{}/text2speech-cred.json".format(proot)
    print("Say something")
    open_stream(current_state_model)
    while True:
        b, s = get_next(current_state_model)
        print(b, s)
        if s.lower().find("stop") != -1:
            break

    close_stream(current_state_model, user_name="main_loop")
    print("Done")
