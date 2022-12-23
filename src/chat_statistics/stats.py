from collections import Counter, defaultdict
from pathlib import Path
from typing import Union

import arabic_reshaper
from bidi.algorithm import get_display
from hazm import Normalizer, sent_tokenize, word_tokenize
from loguru import logger
from src.data import DATA_DIR  # Because of export ${PWD}, src is known
from src.utils.io import read_file, read_json
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
        self.chat_data = read_json(chat_json)
        
        self.normalizer = Normalizer()
        # load stopwords
        logger.info(f"Loading stop words from {DATA_DIR / 'stop_words.txt'}")
        stop_words = read_file(DATA_DIR / 'stop_words.txt').split('\n')
        stop_words = map(str.strip, stop_words)
        self.stop_words = set(map(self.normalizer.normalize, stop_words))

    
    def generate_word_cloud(
        self,
        output_dir: Union[str, Path],
        min_font_size=20, max_font_size=150,
        max_words=800, 
        width: int =1000, height: int =1000,
        backgound_color: str ='white'):
        """Generate a word cloud from the chat data
        :param output_dir: path to output directory for word cloud image
        """
        logger.info("Loading text content...")
        text_content = ''
        for msg in self.chat_data['messages']:
            if type(msg['text']) is str:
                tokens = word_tokenize(msg['text'])
                tokens = filter(lambda item: item not in self.stop_words, tokens)
                text_content += f"\n {' '.join(tokens)}"

            elif type(msg['text']) is list:
                for sub_1 in msg['text']:
                    if type(sub_1) is str:
                        tokens = word_tokenize(sub_1)
                        tokens = filter(lambda item: item not in self.stop_words, tokens)
                        text_content += f"\n {' '.join(tokens)}"
                    elif sub_1['type'] in ['link', 'hashtag', 'mention', 'phone', 'email']:
                        continue
                    else:
                        tokens = word_tokenize(sub_1['text'])
                        tokens = filter(lambda item: item not in self.stop_words, tokens)
                        text_content += f"\n {' '.join(tokens)}"
        
        # normalize reshape for final word cloud
        text_content = self.normalizer.normalize(text_content)
        text = arabic_reshaper.reshape(text_content)
        text = get_display(text)
        
        # generate word cloud
        logger.info("Generating word cloud...")
        wordcloud = WordCloud(
            font_path=str(DATA_DIR / 'courbd.ttf'),
            min_font_size=min_font_size, max_font_size=max_font_size,
            max_words=max_words, 
            width=width, height=height,
            background_color=backgound_color,
            ).generate(text)
        
        logger.info(f"Saving word cloud to {output_dir}...")
        wordcloud.to_file(str(output_dir / 'wordcloud.png'))

    @staticmethod
    def rebuild_msg(sub_message: dict):
        """ convert a message with text type of list to convert a message with text type of string
        :param sub_message: a message includes text with list type
        """
        res_msg = ''
        for item in sub_message['text']:
            if isinstance(item, str):
                res_msg = ' '.join([res_msg, item])
            else:
                res_msg = ' '.join([res_msg, item['text']])
            
        return res_msg


    def msg_has_question(self, msg: dict) -> bool:
        """ return boolean if a message has question elements
        :param msg: any message
        :return: True if message is a question
        """
        if not isinstance(msg['text'], str):
            msg['text'] = self.rebuild_msg(msg)
        
        sentences = sent_tokenize(msg['text'])
        for sentence in sentences:
            if ('?' not in sentence) and ('؟' not in sentence) and ('چرا' not in sentence) and ('آیا' not in sentence):
                continue
            return True


    def id_and_name(self):
        id_and_name = {}
        for msg in self.chat_data['messages']:
            if not msg.get('from_id'):
                continue
            id_and_name[msg['from_id']] = msg['from']
        return id_and_name

    def get_top_answering_users(self, top_n: int) -> dict:
        """ get Active users(not None users) with most messages response
        :param top_n: number of top people to show
        :return: a dictionary with if and number of messages response
        """
        logger.info("Getting top answering users...")
        is_question = defaultdict(bool)

        for msg in self.chat_data['messages']:
            if not isinstance(msg['text'], str):
                msg['text'] = self.rebuild_msg(msg)
                
            sentences = sent_tokenize(msg['text'])
            for sentence in sentences:
                if ('?' not in sentence) and ('؟' not in sentence) and ('چرا' not in sentence) and ('آیا' not in sentence):
                    continue
                is_question[msg['id']] = True
                break


        
        # loads top users
        users = []
        user_names = self.id_and_name()
        for msg in self.chat_data['messages']:
            if not msg.get('reply_to_message_id'):
                continue
          
            if not is_question[msg['reply_to_message_id']]:
                continue
            if user_names[msg['from_id']] is None:
                continue
        
            
            users.append(msg['from_id'])
            top_users = dict(Counter(users).most_common(top_n))
        
        f_top_users = {user_names[k]: v for k,v in top_users.items()}
        print('Top answering users', f_top_users, end='\n\n')
        return f_top_users

    def get_most_talkative_users(self, top_n: int) -> dict:
        """ get Active users(not None users) with most messages response
        :param top_n: number of top people to show
        :return: a dictionary with if and number of messages response
        """
        logger.info("Getting most talkative users...")
        
        # loads top users
        users = []
        user_names = self.id_and_name()
        for msg in self.chat_data['messages']:
            if user_names.get(msg.get('from_id')) is None:
                continue
        
            
            users.append(msg['from_id'])
            top_users = dict(Counter(users).most_common(top_n))
        
        f_top_users = {user_names[k]: v for k,v in top_users.items()}
        print('Most talkative users', f_top_users, end='\n\n')
        return f_top_users
        



if __name__ == "__main__":
    chat_stats = ChatStatistics(chat_json=DATA_DIR / 'chat_telegram.json')
    chat_stats.generate_word_cloud(output_dir=DATA_DIR)
    chat_stats.get_top_answering_users(top_n=10)
    chat_stats.get_most_talkative_users(top_n=10)


    
    print("*********************************************Done!*********************************************")
