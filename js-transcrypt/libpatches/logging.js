//
// mini-patch logger
//

import { repr } from './org.transcrypt.__runtime__.js';


class MinimalLogger
{
    constructor()
    {
        this._enable_debug = false;
        if ( typeof localStorage !== 'undefined' && localStorage != null
             && localStorage !== false
             && localStorage.debug != null && localStorage.debug !== ''
             && /(^|,)logging\*?($|,)/.test(localStorage.debug) ) {
            this._enable_debug = true;
        }
    }

    error(msg, ...args)
    {
        this._emit('[[logging.ERROR]]', ' !! ', msg, args, console.error);
    }

    critical(msg, ...args)
    {
        this._emit('[[logging.CRITICAL]]', ' !! ', msg, args, console.error);
    }

    warning(msg, ...args)
    {
        this._emit('[[logging.WARNING]]', ' ! ', msg, args);
    }
    
    info(msg, ...args)
    {
        this._emit('', '', msg, args);
    }

    debug(msg, ...args)
    {
        if (this._enable_debug) {
            this._emit('logging.debug', ' -- ', msg, args);
        }
    }

    _emit(label, sep, msg, args, log_fn)
    {
        let s = label + sep + msg;
        if (args.length) {
            s += "  //  ";
            s += args.map( (a) => repr(a) ).join(' ; ');
        }
        if (log_fn !== undefined) {
            log_fn(s);
        } else {
            console.log(s);
        }
    }
};


const single_logger_instance = new MinimalLogger();


export function getLogger()
{
    return single_logger_instance;
}

export function basicConfig()
{
}

