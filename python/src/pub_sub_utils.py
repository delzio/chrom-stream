from google.cloud import pubsub_v1
import json
import os

# GCP
CREDENTIALS = os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
PROJECT_ID = os.environ["GCP_PROJECT_ID"]
TOPIC_ID = "chrom-sensor-readings"   # name of topic
SUBSCRIPTION_ID = os.environ["PUBSUB_SUBSCRIPTION_ID"]
publisher = pubsub_v1.PublisherClient()

def publish(message: dict) -> None:
    """ Publish message formatted as dictionary to GCP Pub/Sub """

    topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)

    future = publisher.publish(
        topic_path,
        json.dumps(message).encode("utf-8"),
        source="python_test"
    )

    print(f"publishing data to pubsub: {message}")

def subscribe(callback_fn) -> None:
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_ID)

    print(f"Listening for messages from: {subscription_path}")
    subscriber.subscribe(subscription_path, callback=callback_fn)

    # Keep process running
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("Stopped")


