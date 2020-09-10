#!/usr/bin/python3
import requests
import hashlib
import flask

class Webapp(object):

    _app: flask.Flask
    flask: flask.Flask
    _google_tracking_code: str

    def __init__(self, name, static_directory:str="static", sort_dicts:bool=False, google_tracking_code:str=""):
        self._app = flask.Flask(name, static_folder=static_directory)
        self.flask = self._app
        self._google_tracking_code = google_tracking_code

    def __call__(self):
        print("Not implemented")

    def _handle_404(self, e):
        # Track this event
        self.trackPageFetch("/404")

        return flask.jsonify({
            "success": False,
            "message": "not found",
            "error":str(e)
        }), 404

    def _handle_500(self, e):
        # Track this event
        self.trackError("/error", "500")

        return flask.jsonify({
            "success": False,
            "message":"an application error ocurred",
            "error":str(e)
        }), 500

    def registerDefaultErrorHandlers(self):
        print("Registering default webapp error handlers")
        self._app.error_handler_spec[None][404] = self._handle_404
        self._app.error_handler_spec[None][500] = self._handle_500

    def fetchClientUUID(self) -> str:
        """Fetch the client's browser fingerprint as a hash. Only works inside a request

        Returns:
            str: Client UUID
        """
        return hashlib.md5(flask.request.headers.get('User-Agent').encode()).hexdigest()

    def _ga_collect(self, data: dict):
        try:
            requests.post(
                'https://www.google-analytics.com/collect', data=data)
        except requests.exceptions.ConnectionError as e:
            print("Failed to make tracking request")

    def _ga_track_event(self, category:str, action:str, uid:str=None):
        # Skip if no tracking code is supplied
        if self._google_tracking_code == "":
            return

        # Handle no uid
        if uid == None:
            uid = self.fetchClientUUID()

        # Build collections data
        data = {
            'v': '1',  # API Version.
            'tid': self._google_tracking_code,  # Tracking ID / Property ID.
            # Anonymous Client Identifier. Ideally, this should be a UUID that
            # is associated with particular user, device, or browser instance.
            'cid': uid,
            't': 'event',  # Event hit type.
            'ec': category,  # Event category.
            'ea': action,  # Event action.
            'el': None,  # Event label.
            'ev': 0,  # Event value, must be an integer
            'ua': 'Opera/9.80 (Windows NT 6.0) Presto/2.12.388 Version/12.14'
        }

        self._ga_collect(data)

    def _ga_track_nav_path(self, url: str, uid: str = None):
        # Skip if no tracking code is supplied
        if self._google_tracking_code == "":
            return

        # Handle no uid
        if uid == None:
            uid = self.fetchClientUUID()

        # Build collections data
        data = {
            'v': '1',  # API Version.
            'tid': self._google_tracking_code,  # Tracking ID / Property ID.
            # Anonymous Client Identifier. Ideally, this should be a UUID that
            # is associated with particular user, device, or browser instance.
            'cid': uid,
            't': "pageview",
            'dp': url,
            'ua': 'Opera/9.80 (Windows NT 6.0) Presto/2.12.388 Version/12.14'
        }

        self._ga_collect(data)

    def trackAPICall(self, endpoint: str, uid: str = None):

        # Handle no uid
        if uid == None:
            uid = self.fetchClientUUID()

        # Log the request
        print(f"A request has been made to {endpoint} with a UID of {uid}")

        # Track an event
        self._ga_track_event("APICall", endpoint, uid=uid)

        # Track the page itself
        self._ga_track_nav_path(endpoint, uid=uid)
        


    def trackPageFetch(self, url: str, uid: str = None):
        
        # Handle no uid
        if uid == None:
            uid = self.fetchClientUUID()

        # Log the request
        print(f"A request has been made to {url} with a UID of {uid}")

        # Track the page
        self._ga_track_nav_path(url, uid=uid)

    def trackError(self, endpoint: str, error_code: str, uid: str = None):

        # Handle no uid
        if uid == None:
            uid = self.fetchClientUUID()

        # Log the request
        print(f"A request has been made to {endpoint} with a UID of {uid}")

        # Track an event
        self._ga_track_event("ERROR", f"{endpoint}?internal_error={error_code}", uid=uid)

