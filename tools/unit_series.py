"""Attach franchises using regional SSID game_id and game-title master rows."""
from collections import Counter
import re

JP_TEXT = re.compile(r'[\u3040-\u30ff\u3400-\u9fff]')


def attach_series(master, snapshot, series_sources):
    from build_unit_master import source_snapshot_fingerprint
    if series_sources.get('schema_version') != 1:
        raise ValueError('Unsupported series source schema')
    if series_sources.get('unit_snapshot_fingerprint') != source_snapshot_fingerprint(snapshot):
        raise ValueError('Series mappings use a different reviewed unit snapshot')
    raw = {server: {r['original_id']: r for r in snapshot['sources'][server]['rows']}
           for server in ('GL', 'JP')}
    unknown, untranslated, counts = [], [], Counter()
    for unit in master['units']:
        for identity in unit['identities']:
            server, uid = identity['server'], identity['original_id']
            game_id = str(raw[server][uid]['game_id'])
            mapping = series_sources['mappings'].get(server, {}).get(game_id)
            verified_row = bool(mapping and mapping.get('raw_name') and
                                mapping.get('status') != 'unknown' and game_id != '0')
            series = mapping.get('series') if verified_row else None
            source_id = server + '_game_master'
            source = series_sources['sources'][source_id]
            identity.update(game_id=game_id, series=series,
                            game_title=mapping.get('game_title') if verified_row else None,
                            series_status='known' if series else 'unknown_game_id',
                            series_provenance={
                                'unit_source': server,
                                'unit_source_sha256': snapshot['sources'][server]['sha256'],
                                'unit_form_id': uid, 'unit_field': 'game_id',
                                'game_title_source': source_id,
                                'game_title_source_sha256': source['sha256'],
                                'game_title_row_id': game_id,
                                'game_title_row_verified': verified_row,
                                'raw_game_title': mapping.get('raw_name') if mapping else None,
                                'normalization': mapping.get('normalization') if mapping else None,
                                'label_source': mapping.get('name_source') if mapping else None,
                            })
            if not series:
                unknown.append({'server': server, 'original_id': uid, 'game_id': game_id})
            else:
                counts[series] += 1
                if JP_TEXT.search(series):
                    untranslated.append({'server': server, 'original_id': uid,
                                         'game_id': game_id, 'series': series})
        labels = sorted({i['series'] for i in unit['identities'] if i['series']})
        complete = bool(unit['identities']) and all(i['series'] for i in unit['identities'])
        unit.update(series=labels[0] if len(labels) == 1 and complete else None,
                    series_values=labels,
                    game_titles=sorted({i['game_title'] for i in unit['identities'] if i['game_title']}),
                    series_game_ids=[{'server': i['server'], 'game_id': i['game_id']}
                                     for i in unit['identities']],
                    series_status=('known' if len(labels) == 1 and complete else
                                   'multiple_series' if len(labels) > 1 else
                                   'no_unit_metadata' if not unit['identities'] else 'unknown_game_id'))
    master['series_sources'] = {key: value for key, value in series_sources.items()
                                if key in ('sources', 'series_rule', 'assignment_rule', 'unit_snapshot_fingerprint')}
    master['coverage']['series'] = {
        'regional_identity_count': sum(len(u['identities']) for u in master['units']),
        'known_regional_identities': sum(counts.values()),
        'unknown_game_id_count': len(unknown), 'unknown_game_id_rows': unknown,
        'master_rows_without_series': sum(u['series'] is None for u in master['units']),
        'master_rows_without_unit_metadata': sum(not u['identities'] for u in master['units']),
        'untranslated_series_identity_count': len(untranslated),
        'untranslated_series_values': sorted({r['series'] for r in untranslated}),
        'untranslated_series_rows': untranslated,
        'identities_by_series': dict(sorted(counts.items())),
    }
    return master
