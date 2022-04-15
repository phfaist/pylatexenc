


#
# THIS METHOD CAN ASSUME THAT THERE ARE NO DUPLICATES IN THE LIST.
#
def bisect_right(a, x):
    # find the first index of a that is > pos

    lo = 0
    hi = len(a)
    mid = None

    while True:
        if a[lo] > x:
            return lo
        if a[hi-1] <= x:
            return hi
        if hi - lo <= 2:
            if a[lo+1] > x:
                return lo
            else: #if a[lo+2] > x:
                return lo+1
        mid = (hi + lo) // 2
        if a[mid] > x:
            hi = mid+1
        elif a[mid] <= x:
            lo = mid
