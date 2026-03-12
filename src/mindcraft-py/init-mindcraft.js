import * as Mindcraft from '../mindcraft/mindcraft.js';
import settings from '../../settings.js';
import yargs from 'yargs';
import { hideBin } from 'yargs/helpers';

function parseArguments() {
    return yargs(hideBin(process.argv))
        .option('mindserver_port', {
            type: 'number',
            describe: 'Mindserver port',
            default: settings.mindserver_port
        })
        .help()
        .alias('help', 'h')
        .parse();
}

const args = parseArguments();

settings.mindserver_port = args.mindserver_port;

console.log('[DEBUG] init-mindcraft env check:', {
    OPENAI_API_KEY: process.env.OPENAI_API_KEY ? 'Present' : 'Missing',
    DOUBAO_API_KEY: process.env.DOUBAO_API_KEY ? 'Present' : 'Missing',
    DEEPSEEK_API_KEY: process.env.DEEPSEEK_API_KEY ? 'Present' : 'Missing'
});

// init(host_public, port, auto_open_ui)
Mindcraft.init(false, settings.mindserver_port, false);

console.log(`Mindcraft initialized with MindServer at localhost:${settings.mindserver_port}`); 