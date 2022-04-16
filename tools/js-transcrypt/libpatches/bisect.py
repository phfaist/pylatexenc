


#
# THIS METHOD CAN ASSUME THAT THERE ARE NO DUPLICATES IN THE LIST.
#
def bisect_right(a, x):
    # find the first index of a that is > pos

    lo = 0
    hi = len(a)
    mid = None

    while True:

        #print(f"{a=} {x=} :: {lo=} {hi=}  (mid was {mid=})")

        if a[lo] > x:
            return lo
        if a[hi-1] <= x:
            return hi

        # we know that  a[lo] <= x  and  a[hi-1] > x

        if hi - lo <= 2:
            if a[lo+1] > x:  # a[lo] <= x  and a[lo+1] > x  -->  return lo+1
                return lo+1
            else: #if a[lo+2] > x:
                return lo+2

        mid = (hi + lo) // 2
        if a[mid] > x:
            hi = mid+1  # we still have  a[hi-1] > x
        else: # i.e., if a[mid] <= x:
            lo = mid  # we still have a[lo] <= x
