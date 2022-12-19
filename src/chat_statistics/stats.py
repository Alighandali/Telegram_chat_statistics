import json
from pathlib import Path
from typing import Union

import arabic_reshaper
from bidi.algorithm import get_display
from hazm import Normalizer, word_tokenize
from loguru import logger
from src.data import DATA_DIR  # Because of export ${PWD}, src is known
from wordcloud import WordCloud


class ChatStatistics:
    """ Generates chat statistics from a telegram caht json file
    """
    def __init__(self, chat_json: Union[str, Path]):
        """
        :param chat_json: path to telegram export json file
        """
        # load chat data
        logger.info(f"Loading chat data from {chat_json}")
        with open(chat_json) as f:
            self.chat_data = json.load(f)
        
        self.normalizer = Normalizer()
        # load stopwords
        logger.info(f"Loading stop words from {DATA_DIR / 'stop_words.txt'}")
        with open(DATA_DIR / 'stop_words.txt') as sw:
            stop_words = sw.readlines()
        stop_words = list(map(str.strip, stop_words))
        self.stop_words = list(map(self.normalizer.normalize, stop_words))

    def generate_word_cloud(
        self,
        output_dir: Union[str, Path],
        width: int =1000, height: int =1000,
        max_font_size: int =250,
        backgound_color: str ='white'):
        """Generates a word cloud from the chat data
        :param output_dir: path to output directory for word cloud image
        """
        logger.info("Lading text content...")
        text_content = ''
        for msg in self.chat_data['messages']:
            if type(msg['text']) is str:
                # tokens = word_tokenize(msg['text'])
                # tokens = filter(lambda item: item not in self.stop_words, tokens)
                # text_content += f"\n {' '.join(tokens)}"
                text_content += f"\n {' '.join(msg['text'])}"

            elif type(msg['text']) is list:
                for sub_1 in msg['text']:
                    if type(sub_1) is str:
                        # tokens = word_tokenize(sub_1)
                        # tokens = filter(lambda item: item not in self.stop_words, tokens)
                        # text_content += f"\n {' '.join(tokens)}"
                        text_content += f"\n {' '.join(sub_1)}"
                    elif sub_1['type'] in ['code', 'link']:
                        pass
                    else:
                        # tokens = word_tokenize(sub_1['text'])
                        # tokens = filter(lambda item: item not in self.stop_words, tokens)
                        # text_content += f"\n {' '.join(tokens)}"
                        text_content += f"\n {' '.join(sub_1['text'])}"
        
        # normalize reshape for final word cloud
        text_content = self.normalizer.normalize(text_content)
        text = arabic_reshaper.reshape(text_content)
        text = get_display(text)
        
        # generate word cloud
        logger.info("Generating word cloud...")
        wordcloud = WordCloud(
            font_path=str(DATA_DIR / 'courbd.ttf'),
            width=width, height=height,
            max_font_size=max_font_size,
            background_color=backgound_color,
            stopwords=self.stop_words # WordCloud can filter stopword itself
            ).generate(text)
        
        logger.info(f"Saving word cloud to {output_dir}...")
        wordcloud.to_file(str(output_dir / 'wordcloud.png'))





if __name__ == "__main__":
    chat_stats = ChatStatistics(chat_json=DATA_DIR / 'result_telegram.json')
    chat_stats.generate_word_cloud(output_dir=DATA_DIR)
    
    print("Done!")
