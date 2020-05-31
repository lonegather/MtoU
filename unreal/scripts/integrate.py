import os
import sys
import json
import unreal


def get_asset_tools():
    return unreal.AssetToolsHelpers.get_asset_tools()


def get_assets(*args, **kwargs):
    return unreal.AssetRegistryHelpers.get_asset_registry().get_assets(unreal.ARFilter(*args, **kwargs))


def get_assets_by_class(class_name):
    return unreal.AssetRegistryHelpers.get_asset_registry().get_assets_by_class(class_name)


def spawn_actor_from_object(object_to_use):
    return unreal.EditorLevelLibrary.spawn_actor_from_object(object_to_use, unreal.Vector())


def spawn_actor_from_class(class_to_use):
    return unreal.EditorLevelLibrary.spawn_actor_from_class(class_to_use, unreal.Vector())


def get_option(data):
    stage = data['stage']
    option = unreal.FbxImportUI()
    option.set_editor_property('create_physics_asset', True)
    option.set_editor_property('import_animations', bool(stage in ['lyt', 'anm']))
    option.set_editor_property('import_as_skeletal', bool(stage in ['skn', 'rig']))
    option.set_editor_property('import_materials', bool(stage in ['mdl']))
    option.set_editor_property('import_mesh', bool(stage in ['mdl', 'skn', 'rig']))
    option.set_editor_property('import_textures', bool(stage in ['mdl']))
    option.set_editor_property('mesh_type_to_import', unreal.FBXImportType.FBXIT_STATIC_MESH)

    if stage in ['mdl']:
        option.static_mesh_import_data.set_editor_property('convert_scene', True)
        option.static_mesh_import_data.set_editor_property('convert_scene_unit', True)
        option.static_mesh_import_data.set_editor_property('import_uniform_scale', 1.0)

    elif stage in ['skn', 'rig']:
        for asset_data in get_assets_by_class('Skeleton'):
            if data['skeleton'] in str(asset_data.asset_name):
                skeleton = asset_data.get_asset()
                break
        else:
            skeleton = None
        option.set_editor_property('skeleton', skeleton)
        option.skeletal_mesh_import_data.set_editor_property('convert_scene', True)
        option.skeletal_mesh_import_data.set_editor_property('convert_scene_unit', True)
        option.skeletal_mesh_import_data.set_editor_property('import_uniform_scale', 1.0)
        option.skeletal_mesh_import_data.set_editor_property('import_morph_targets', True)
        option.skeletal_mesh_import_data.set_editor_property('update_skeleton_reference_pose', True)
        option.skeletal_mesh_import_data.set_editor_property('use_t0_as_ref_pose', True)

    elif stage in ['lyt', 'anm']:
        for asset_data in get_assets_by_class('Skeleton'):
            if data['skeleton'] in str(asset_data.asset_name):
                skeleton = asset_data.get_asset()
                break
        else:
            unreal.log_error('No skeleton named \'%s\' found.')
            return None
        option.set_editor_property('skeleton', skeleton)
        option.anim_sequence_import_data.set_editor_property('custom_sample_rate', data['shot']['fps'])
    return option


def import_fbx(data):
    task = unreal.AssetImportTask()
    task.set_editor_property('automated', True)
    task.set_editor_property('destination_path', data['target'])
    task.set_editor_property('filename', data['source'])
    task.set_editor_property('options', get_option(data))
    task.set_editor_property('replace_existing', True)
    task.set_editor_property('save', False)
    get_asset_tools().import_asset_tasks([task])

    if data['stage'] in ['skn', 'rig']:
        bp_name = os.path.basename(data['source']).split('_skn')[0]
        bp_path = '%s/%s' % (data['target'], bp_name)
        if bp_name and not unreal.EditorAssetLibrary.does_asset_exist(bp_path):
            bp_asset = get_asset_tools().create_asset(
                asset_name=bp_name,
                package_path=data['target'],
                asset_class=unreal.Blueprint,
                factory=unreal.BlueprintFactory()
            )
            get_asset_tools().open_editor_for_assets([bp_asset])

    unreal.EditorAssetLibrary.save_directory(data['target'])


def setup_sequencer(source, target, shot):
    world_name = os.path.basename(source).split('anm_MainCam_')[0] + 'world'
    sequencer_name = os.path.basename(source).split('_anm_MainCam_')[0]
    level_path = '%s/%s' % (target, world_name)

    # setup level world
    world = unreal.EditorLoadingAndSavingUtils.load_map(level_path)
    if unreal.EditorLevelLibrary.get_editor_world().get_name() != world_name:
        unreal.EditorLevelLibrary.new_level(level_path)
        world = unreal.EditorLoadingAndSavingUtils.load_map(level_path)

    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        if actor.get_class().get_name() in ['CineCameraActor', 'LevelSequenceActor']:
            unreal.EditorLevelLibrary.destroy_actor(actor)

    # setup level sequencer
    level_sequence_path = '%s/%s' % (target, sequencer_name)
    if unreal.EditorAssetLibrary.does_asset_exist(level_sequence_path):
        unreal.EditorAssetLibrary.delete_asset(level_sequence_path)
    level_sequence = unreal.LevelSequence.cast(get_asset_tools().create_asset(
        asset_name=sequencer_name,
        package_path=target,
        asset_class=unreal.LevelSequence,
        factory=unreal.LevelSequenceFactoryNew()
    ))

    level_sequence.set_tick_resolution(unreal.FrameRate(shot['fps']))
    level_sequence.set_display_rate(unreal.FrameRate(shot['fps']))
    level_sequence.set_playback_start(shot['start'])
    level_sequence.set_view_range_start(shot['start']/shot['fps'])
    level_sequence.set_work_range_start((shot['start']+1.0)/shot['fps'])
    level_sequence.set_playback_end(shot['end']+1.0)
    level_sequence.set_view_range_end((shot['end']+1.0)/shot['fps'])
    level_sequence.set_work_range_end((shot['end']+1.0)/shot['fps'])

    # setup each character in this shot
    bp_assets_data = get_assets(
        class_names=['Blueprint'],
        package_paths=['/Game/'],
        recursive_paths=True,
    )

    # This is all the blueprint assets need to be put in the current shot level
    sequence_assets = get_assets_by_class('AnimSequence')
    bp_assets = [bp_data.get_asset() for bp_data in bp_assets_data if bp_data.asset_name in shot['chars']]
    all_actors = unreal.EditorLevelLibrary.get_all_level_actors()

    for asset in bp_assets:
        for sequence_asset in [asset_data.get_asset() for asset_data in sequence_assets]:
            if not sequence_asset.get_name() in shot['anims']: continue
            if sequence_asset.get_name().endswith(asset.get_name()): break
        else:
            unreal.log_error('AnimSequence for \'%s\' does not exist.' % asset.get_name())
            return

        for actor in all_actors:
            if actor.get_name().count(asset.get_name()):
                break
        else:
            actor = spawn_actor_from_object(asset)

        binding = level_sequence.add_possessable(actor.get_component_by_class(unreal.SkeletalMeshComponent))
        anim_track = unreal.MovieSceneBindingExtensions.add_track(binding, unreal.MovieSceneSkeletalAnimationTrack)
        anim_section = anim_track.add_section()
        anim_section.set_range(shot['start'], shot['end']+1.0)
        anim_section.set_row_index(0)
        anim_section.get_editor_property('params').set_editor_property('animation', sequence_asset)

    # setup camera
    import_setting = unreal.MovieSceneUserImportFBXSettings()
    import_setting.set_editor_property('create_cameras', False)
    import_setting.set_editor_property('force_front_x_axis', False)
    import_setting.set_editor_property('match_by_name_only', True)
    import_setting.set_editor_property('reduce_keys', False)
    import_setting.set_editor_property('reduce_keys_tolerance', 0.001)

    cine_camera = unreal.CineCameraActor.cast(spawn_actor_from_class(unreal.CineCameraActor))
    cine_camera.set_actor_label('ShotCam')
    cine_camera_component = cine_camera.get_cine_camera_component()
    filmback_settings = cine_camera_component.get_editor_property('filmback')
    filmback_settings.set_editor_property('sensor_width', shot['aperture_width'])
    filmback_settings.set_editor_property('sensor_height', shot['aperture_height'])
    focus_settings = cine_camera_component.get_editor_property('focus_settings')
    try:
        focus_method = unreal.CameraFocusMethod.MANUAL if shot['focus'] else unreal.CameraFocusMethod.DISABLE
    except AttributeError:
        focus_method = unreal.CameraFocusMethod.MANUAL if shot['focus'] else unreal.CameraFocusMethod.NONE
    focus_settings.set_editor_property('focus_method', focus_method)
    binding = level_sequence.add_possessable(cine_camera)
    level_sequence.add_possessable(cine_camera_component)

    camera_id = unreal.MovieSceneObjectBindingID()
    camera_id.set_editor_property('guid', binding.get_id())
    camera_cut_track = level_sequence.add_master_track(unreal.MovieSceneCameraCutTrack)
    camera_section = camera_cut_track.add_section()
    camera_section.set_range(shot['start'], shot['end']+1.0)
    camera_section.set_camera_binding_id(camera_id)
    unreal.SequencerTools.import_fbx(world, level_sequence, [binding], import_setting, source)

    # save modifications
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    unreal.EditorLoadingAndSavingUtils.load_map(level_path)
    get_asset_tools().open_editor_for_assets([level_sequence])
    unreal.LevelSequenceEditorBlueprintLibrary.set_current_time(shot['start'])
    spawn_actor_from_object(level_sequence)
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)


def main():
    option_file = sys.argv[1]
    with open(option_file) as option:
        data = json.load(option)
        data['target'] = data['target'][:-1] if data['target'][-1] in ['\\', '/'] else data['target']

    print('=' * 120)
    for k, v in data.items():
        print('| [%s] --- %s' % (k, v))
    print('-' * 120)

    if data['stage'] != 'cam':
        import_fbx(data)
    else:
        setup_sequencer(data['source'], data['target'], data['shot'])

    print('| Successfully imported.')
    print('=' * 120)


if __name__ == '__main__':
    main()
