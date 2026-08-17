with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

marker = 'if __name__ == "__main__":'
idx = content.index(marker)

profile_output = '''
    # Profiling output
    if _simulation_times:
        avg_sim = sum(_simulation_times) / len(_simulation_times) * 1000
        max_sim = max(_simulation_times) * 1000
        print(f"Simulation: avg={avg_sim:.2f}ms, max={max_sim:.2f}ms over {len(_simulation_times)} frames")
    if _render_times:
        avg_render = sum(_render_times) / len(_render_times) * 1000
        max_render = max(_render_times) * 1000
        print(f"Render: avg={avg_render:.2f}ms, max={max_render:.2f}ms over {len(_render_times)} frames")
    total_frames = len(_frame_times)
    if total_frames > 1:
        total_time = _frame_times[-1] - _frame_times[0]
        avg_fps = (total_frames - 1) / total_time
        print(f"Overall: {total_frames} frames in {total_time:.2f}s = {avg_fps:.1f} FPS")
'''

content = content[:idx] + profile_output + '\n' + content[idx:]

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Added profiling output')
