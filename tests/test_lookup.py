from __future__ import unicode_literals

import mock

import pytest

import spotify


def test_lookup_of_invalid_uri(session_mock, provider, caplog):
    session_mock.get_link.side_effect = ValueError('an error message')

    results = provider.lookup('invalid')

    assert len(results) == 0
    assert 'Failed to lookup "invalid": an error message' in caplog.text()


def test_lookup_of_unhandled_uri(session_mock, provider, caplog):
    sp_link_mock = mock.Mock(spec=spotify.Link)
    sp_link_mock.type = spotify.LinkType.INVALID
    session_mock.get_link.return_value = sp_link_mock

    results = provider.lookup('something')

    assert len(results) == 0
    assert (
        'Failed to lookup "something": Cannot handle <LinkType.INVALID: 0>'
        in caplog.text())


@pytest.mark.xfail
def test_lookup_when_offline(session_mock, sp_track_mock, provider, caplog):
    session_mock.get_link.return_value = sp_track_mock.link
    sp_track_mock.link.as_track.return_value.load.side_effect = spotify.Error(
        'Must be online to load objects')

    results = provider.lookup('spotify:track:abc')

    assert len(results) == 0
    assert (
        'Failed to lookup "spotify:track:abc": Must be online to load objects'
        in caplog.text())


def test_lookup_of_track_uri(session_mock, sp_track_mock, web_client_mock,
                             web_track_lookup_mock, provider):
    session_mock.get_link.return_value = sp_track_mock.link
    web_client_mock.get.return_value = web_track_lookup_mock

    results = provider.lookup('spotify:track:abc')

    assert len(results) == 1
    track = results[0]
    assert track.uri == 'spotify:track:abc'
    assert track.name == 'ABC 123'
    assert track.bitrate == 160


def test_lookup_of_album_uri(session_mock, sp_album_browser_mock,
                             web_client_mock, web_album_lookup_mock, provider):
    sp_album_mock = sp_album_browser_mock.album
    session_mock.get_link.return_value = sp_album_mock.link
    web_client_mock.get.return_value = web_album_lookup_mock

    results = provider.lookup('spotify:album:def')

    assert len(results) == 2
    track = results[0]
    assert track.uri == 'spotify:track:abc'
    assert track.name == 'ABC 123'
    assert track.bitrate == 160


def test_lookup_of_artist_uri(session_mock, sp_artist_browser_mock,
                              sp_album_browser_mock, web_client_mock,
                              web_artist_albums_mock, web_album_lookup_mock,
                              provider):
    sp_artist_mock = sp_artist_browser_mock.artist
    session_mock.get_link.return_value = sp_artist_mock.link

    web_client_mock.get.side_effect = (web_artist_albums_mock,
                                       web_album_lookup_mock)

    # TODO: This gets duplicate tracks, do we care?
    results = provider.lookup('spotify:artist:abba')

    assert len(results) == 4
    track = results[0]
    assert track.uri == 'spotify:track:abc'
    assert track.name == 'ABC 123'
    assert track.bitrate == 160


def test_lookup_of_playlist_uri(session_mock, sp_playlist_mock, provider):
    session_mock.get_link.return_value = sp_playlist_mock.link

    results = provider.lookup('spotify:playlist:alice:foo')

    session_mock.get_link.assert_called_once_with('spotify:playlist:alice:foo')
    sp_playlist_mock.link.as_playlist.assert_called_once_with()
    sp_playlist_mock.load.assert_called_once_with(10)
    sp_playlist_mock.tracks[0].load.assert_called_once_with(10)

    assert len(results) == 1
    track = results[0]
    assert track.uri == 'spotify:track:abc'
    assert track.name == 'ABC 123'
    assert track.bitrate == 160


def test_lookup_of_starred_uri(session_mock, sp_starred_mock, provider):
    session_mock.get_link.return_value = sp_starred_mock.link

    results = provider.lookup('spotify:user:alice:starred')

    session_mock.get_link.assert_called_once_with('spotify:user:alice:starred')
    sp_starred_mock.link.as_playlist.assert_called_once_with()
    sp_starred_mock.load.assert_called_once_with(10)

    assert len(results) == 2
    track = results[0]
    assert track.uri == 'spotify:track:newest'
    assert track.name == 'Newest'
    assert track.bitrate == 160
