public class Main{
    public static void main(String[] args) {
        int[] array = {-1,2,-3,3};
        x =value(array);
        System.out.println(x);
    }

    public static int value(int[] aray){
        for (int i=0;i<array.length;i++){
            for (int j = i;j<array.length;j++){
                if (aray[i]==abs(array[j])){
                    return aray[i];
                }
                else{
                    return -1;
                }
            }
        }

    }
}