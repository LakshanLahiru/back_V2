list1= [2,2,1,1,3]
arr = [1,2]
arr1 = [-3,0,1,-3,1,1,1,-3,10,0]


def isunique(list1):
    arr2= set()
    arra3 = []
    count=[]
    for i in range(0,len(list1)):

        
        count= [list1.count(list1[i]) for j in range((i+1),len(list1)) if not list1[j]in arra3]
        arra3.append(list1[i])
        print(count)

    
    return count


x=  isunique(list1)
print(x)

