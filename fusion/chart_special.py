"""Publicly specified special-group classifications, independent implementation."""
from .chart_indicators import validate, element_groups, color_groups, digit_presence_groups

DOUBLE_NUMBERS=[11,22,33,44,55,66,77]
REVERSED=[(n,(n%10)*10+n//10) for n in range(1,81) if n%10!=0 and n>=10 and n%10*10+n//10<=80]
REVERSED+= [(n,n*10) for n in range(1,9)]
REVERSED=sorted(set(tuple(sorted(p)) for p in REVERSED if p[0]!=p[1]))
REVERSED_NUMBERS=set(n for pair in REVERSED for n in pair)

def special_groups():
    groups={}
    for k,v in element_groups().items():groups["element_"+k]=sorted(v)
    for k,v in color_groups().items():groups["color_"+k]=sorted(v)
    groups["double"]=DOUBLE_NUMBERS[:]
    groups["reverse"]=sorted(REVERSED_NUMBERS)
    # Complement to digit-swaps + diagonal doubles, with distinct members.
    groups["neither"]=sorted(set(range(1,81))-REVERSED_NUMBERS-set(DOUBLE_NUMBERS))
    for i in range(4):
        groups["sum81_"+str(i+1)]=sorted(n for a in range(i*10+1,(i+1)*10+1) for n in (a,81-a))
    for i,nums in enumerate(digit_presence_groups()):
        groups["has_digit_"+str(i)]=sorted(nums)
    return groups

def special_profile(draw):
    drawn=set(validate(draw))
    return {k:len(drawn.intersection(v)) for k,v in special_groups().items()}
