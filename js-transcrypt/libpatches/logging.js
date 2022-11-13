//
// mini-patch logger
//

import { repr } from './org.transcrypt.__runtime__.js';

import debug_module from 'debug';

debug_module.formatters.r = (v) => repr(v);


class DebugLogger
{
    constructor(scope)
    {
        this.scope = scope;

        this._debug_fn = debug_module(this.scope);
        this._debug_fn_star = debug_module(this.scope+'*'); // always output

        console.debug(`setting up logger ‘${this.scope}’ via debug()`);

        this.error = (msg, ...args) => {
            this._debug_fn_star('[[logging.ERROR]] !! ' + msg, ...args);
        };

        this.critical = (msg, ...args) => {
            this._debug_fn_star('[[logging.CRITICAL]] !! ' + msg, ...args);
        };

        this.warning = (msg, ...args) => {
            this._debug_fn_star('[[logging.WARNING]] !! ' + msg, ...args);
        };
    
        this.info = (msg, ...args) => {
            this._debug_fn_star(msg, ...args);
        };

        this.debug = (msg, ...args) => {
            this._debug_fn('logging.debug ~~ ' + msg, ...args);
        };
    }

    _emit(label, sep, msg, args, log_fn)
    {
        let s = label + sep + _assemble_msg(msg, args);
        if (log_fn !== undefined) {
            log_fn(s);
        } else {
            console.log(s);
        }
    }
};

function _assemble_msg(msg, args)
{
    if (args.length) {
        return msg + "  //  " + args.map( (a) => repr(a) ).join(' ; ');
    }
    return msg;
}



let _logger_instances = {};

export function getLogger(scope)
{
    let logger = _logger_instances[scope];
    if (logger == null) { // null or undefined
        logger = new DebugLogger(scope);
        _logger_instances[scope] = logger;
    }
    return logger;
}

export function basicConfig()
{
}

