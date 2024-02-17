import os
import subprocess


def get_countable_unit_string(count: int, unit: str):
	ret = f"{count} {unit}"
	if count != 1:
		ret += "s"
	return ret


def run(
	command,
	capture_output=False,
	print_command=False,
	print_output=False,
	timeout=None,
	text=True,
	arm=False,
):
	if text:
		read = "r"
		write = "w"
	else:
		read = "rb"
		write = "wb"
	with open(".cmd-stdout", write) as fout, open(".cmd-stderr", write) as ferr:
		if arm:
			command = "qemu-arm -L /usr/arm-linux-gnueabihf/ " + command
		sp = subprocess.run(
			command,
			shell=True,
			stdout=fout,
			stderr=ferr,
			text=text or print_output,
			timeout=timeout,
		)
	# TODO configurable max size
	if os.path.getsize(".cmd-stdout") > 100000000 or os.path.getsize(".cmd-stderr") > 100000000:
		# TODO unhack and properly return error
		sp.stdout = "stdout too big"
		sp.stderr = "stderr too big"
	else:
		with open(".cmd-stdout", read) as fout, open(".cmd-stderr", read) as ferr:
			sp.stdout = fout.read()
			sp.stderr = ferr.read()

	if print_command:
		print(f"$ {command}")
	if print_output:
		print(str(sp.stdout))
		print(str(sp.stderr))
	return sp
