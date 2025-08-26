/*** PhF/PYLATEXENC - BEGIN CUSTOM PATCHES ***/

//
// Patch Transcrypt's implementations of some builtin object methods.
//
String.prototype.startswith = function (prefix, start) {
    //console.log("Custom startswith()! prefix = ", prefix, ", start = ", start);
    var pos_start = (typeof start === 'undefined' ? 0 : start);
    if (prefix instanceof Array) {
        for (var i=0;i<prefix.length;i++) {
            if (this.substring(pos_start, pos_start+prefix[i].length) === prefix [i]) {
                return true;
            }
        }
    } else {
        return (this.substring(pos_start, pos_start+prefix.length) === prefix);
    }
    return false;
};
String.prototype.count = function (ch) {
    var i = 0;
    var count = 0;
    for(; i < this.length; ++i) {
        if (ch == this[i]) {
            ++count;
        }
    }
    return count;
};
String.prototype.rjust = function(width, fill_char) {
    if (this.length >= width) {
        return this;
    }
    return fill_char.repeat(width - this.length) + this;
};
String.prototype.rstrip = function(chars) {
    if (chars === undefined) {
        return this.replace (/\s*$/g, '');
    }
    var s = this;
    while (s.length && chars.indexOf(s.slice(-1)) !== -1) {
        s = s.slice(0, -1);
    }
    return s;
}
//
// Patch Transcrypt's __pop__() method which has a bug
// (https://github.com/QQuick/Transcrypt/issues/827)
//
__pop__ = function (aKey, aDefault) {
    var result = this [aKey];
    if (result !== undefined) {
        delete this [aKey];
        return result;
    } else {
        if ( aDefault === undefined ) {
            throw KeyError (aKey, new Error());
        }
    }
    return aDefault;
}

//
// Check that a is not null, too, otherwise we get errors with "'__eq__' in a".
// Also check for __eq__ in b object!
//
__eq__ = function (a, b) {
    if (typeof a == 'object' && a != null && '__eq__' in a) {
        return a.__eq__ (b);
    } else if (typeof b == 'object' && b != null && '__eq__' in b) {
        return b.__eq__ (a);
    } else {
        return a == b;
    }
};





/*** PhF/PYLATEXENC - END CUSTOM PATCHES ***/
