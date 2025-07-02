import os
import sys

# Execute deletion immediately on import
if __name__ == "__main__" or True:
    files_to_delete = [
        "check_and_restart.py",
        "check_imports.py",
        "cleanup_root_files.py",
        "complete_root_cleanup.py",
        "debug_pipeline_init.py",
        "DELETED_check_and_restart.py",
        "execute_cleanup.py",
        "final_root_cleanup.py",
        "internal_diagnostic.py",
        "manual_test.py",
        "minimal_app.py",
        "quick_start_test.py",
        "remove_test_files.py",
        "restart_app_with_fixes.py",
        "restart_fixed_app.py",
        "run_diagnostic.py",
        "standalone_diagnostic.py",
        "start_app_direct.py",
        "start_app_safe.py",
        "start_production.py",
        "syntax_test.py",
        "test_api_direct.py",
        "test_app_import.py",
        "test_krk_fix.py",
        "test_lazy_init.py",
        "test_pipeline_simple.py",
        "CLEANUP_STATUS.md",
        "delete_test_files_now.py"
    ]

    # Change to Theodore directory
    theodore_path = "/Users/antoinedubuc/Desktop/AI_Goodies/Theodore"
    if os.path.exists(theodore_path):
        os.chdir(theodore_path)
    
    deleted_count = 0
    for file in files_to_delete:
        file_path = os.path.join(theodore_path, file)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"✅ Deleted: {file}")
                deleted_count += 1
            except Exception as e:
                print(f"❌ Failed to delete {file}: {e}")
        else:
            print(f"⚠️  File not found: {file}")
    
    print(f"\n🎯 Total files deleted: {deleted_count}")
    
    # Also clean up the deletion scripts
    for cleanup_file in ["delete_test_files.py", "delete_test_files.sh", "execute_deletion.py"]:
        cleanup_path = os.path.join(theodore_path, cleanup_file)
        if os.path.exists(cleanup_path) and cleanup_file != "execute_deletion.py":
            try:
                os.remove(cleanup_path)
                print(f"✅ Also deleted cleanup script: {cleanup_file}")
            except:
                pass