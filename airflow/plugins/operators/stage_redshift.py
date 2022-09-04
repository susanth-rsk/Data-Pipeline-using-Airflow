from airflow.hooks.postgres_hook import PostgresHook
from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults

class StageToRedshiftOperator(BaseOperator):
    ui_color = '#358140'
    
    template_fields = ("s3_key",)
    query_copy = """
        COPY {}
        FROM '{}'
        ACCESS_KEY_ID '{}'
        SECRET_ACCESS_KEY '{}'
        {}
    """    

    @apply_defaults
    def __init__(self,
                 aws_credentials_id,
                 redshift_conn_id,
                 table,
                 s3_bucket,
                 s3_key,
                 file_format="json",
                 json_path="auto",
                 delimiter=",",
                 ignore_headers=1,
                 *args, **kwargs):

        super(StageToRedshiftOperator, self).__init__(*args, **kwargs)
        self.aws_credentials_id = aws_credentials_id
        self.redshift_conn_id = redshift_conn_id
        self.table = table
        self.s3_bucket = s3_bucket
        self.s3_key = s3_key
        self.file_format = file_format        
        self.json_path = json_path
        self.delimiter = delimiter
        self.ignore_headers = ignore_headers  

    def execute(self, context):
        
        self.log.info("Establishing connection to AWS and Redshift")
        aws_hook = AwsHook(self.aws_credentials_id)
        credentials = aws_hook.get_credentials()
        redshift = PostgresHook(postgres_conn_id=self.redshift_conn_id)

        self.log.info("Clearing previously existing data, if any from the Redshift table")
        redshift.run("DELETE FROM {}".format(self.table))

        self.log.info("Copying data from S3 to Redshift")
        if self.file_format == "json":
            file_type = "JSON '{}'".format(self.json_path)
        elif self.file_format == "csv":
            file_type = "IGNOREHEADER '{}' DELIMITER '{}'".format(self.ignore_header, self.delimiter)
        
        formatted_key = self.s3_key.format(**context)
        path_s3 = "s3://{}/{}".format(self.s3_bucket, formatted_key)
        query_formatted = StageToRedshiftOperator.query_copy.format(
            self.table,
            path_s3,
            credentials.access_key,
            credentials.secret_key,
            file_type
        )
        redshift.run(query_formatted)





