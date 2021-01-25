package s3_presign_ipv6;

import com.amazonaws.AmazonServiceException;
import com.amazonaws.HttpMethod;
import com.amazonaws.SdkClientException;
//import com.amazonaws.auth.InstanceProfileCredentialsProvider;
import com.amazonaws.auth.AWSStaticCredentialsProvider;
import com.amazonaws.auth.BasicAWSCredentials;
import com.amazonaws.regions.Regions;
import com.amazonaws.services.s3.AmazonS3;
import com.amazonaws.services.s3.AmazonS3ClientBuilder;
import com.amazonaws.services.s3.model.GeneratePresignedUrlRequest;

import java.io.IOException;
import java.net.URL;

public class App {

    public static void main(String[] args) throws IOException {
        Regions clientRegion = Regions.CN_NORTHWEST_1;
        String bucketName = "billing-cur-langyu";
        String objectKey = "curtest/CUR/20210101-20210201/CUR-Manifest.json";
        BasicAWSCredentials awsCreds = new BasicAWSCredentials("Your-AK", "Your-SK");

        try {
            AmazonS3 s3Client = AmazonS3ClientBuilder.standard()
                //.withCredentials(new InstanceProfileCredentialsProvider(false))
                .withCredentials(new AWSStaticCredentialsProvider(awsCreds))
                .withRegion(clientRegion)
                .withDualstackEnabled(true)
                .build();

            // Set the pre-signed URL to expire after one hour.
            java.util.Date expiration = new java.util.Date();
            long expTimeMillis = expiration.getTime();
            expTimeMillis += 3600000;
            expiration.setTime(expTimeMillis);

            // Generate the pre-signed URL.
            System.out.println("Generating pre-signed URL.");
            GeneratePresignedUrlRequest generatePresignedUrlRequest = new GeneratePresignedUrlRequest(bucketName, objectKey)
                .withMethod(HttpMethod.GET)
                .withExpiration(expiration);
            URL url = s3Client.generatePresignedUrl(generatePresignedUrlRequest);
            System.out.println(url.toString());

            System.exit(0);

        } catch (AmazonServiceException e) {
            // The call was transmitted successfully, but Amazon S3 couldn't process
            // it, so it returned an error response.
            e.printStackTrace();
        } catch (SdkClientException e) {
            // Amazon S3 couldn't be contacted for a response, or the client
            // couldn't parse the response from Amazon S3.
            e.printStackTrace();
        }
    }
}
