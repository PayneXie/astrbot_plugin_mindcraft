import OpenAIApi from 'openai';
import { getKey } from '../utils/keys.js';
import { strictFormat } from '../utils/text.js';

export class Doubao {
    static prefix = 'doubao';
    constructor(model_name, url, params) {
        this.model_name = model_name;
        this.params = params;
        let config = {};
        config.baseURL = url || 'https://ark.cn-beijing.volces.com/api/v3';
        config.apiKey = getKey('DOUBAO_API_KEY');
        this.openai = new OpenAIApi(config);
    }

    async sendRequest(turns, systemMessage, stop_seq='***') {
        let messages = [{'role': 'system', 'content': systemMessage}].concat(turns);
        messages = strictFormat(messages);
        const pack = {
            model: this.model_name,
            messages,
            stop: stop_seq,
            ...(this.params || {})
        };
        let res = null;
        try {
            console.log('Awaiting doubao api response...')
            let completion = await this.openai.chat.completions.create(pack);
            if (completion.choices[0].finish_reason == 'length')
                throw new Error('Context length exceeded'); 
            console.log('Received.')
            res = completion.choices[0].message.content;
        }
        catch (err) {
            if ((err.message == 'Context length exceeded' || err.code == 'context_length_exceeded') && turns.length > 1) {
                console.log('Context length exceeded, trying again with shorter context.');
                return await this.sendRequest(turns.slice(1), systemMessage, stop_seq);
            } else {
                console.log(err);
                res = 'My brain disconnected, try again.';
            }
        }
        return res;
    }

    async embed(text) {
        // Doubao embeddings might be supported, but for now we throw error or implement generic openai embedding if needed
        // Assuming user might use a different embedding model or doubao's if compatible
        throw new Error('Embeddings are not supported by Doubao class yet.');
    }
}
